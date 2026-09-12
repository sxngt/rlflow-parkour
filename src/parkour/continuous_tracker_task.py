"""New shared-surface Tracker prototype; independent of the legacy jump task."""
import copy,math
import torch
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply_inverse
from parkour.task import FootholdCfg,FootholdEnv
from isaaclab_assets import UNITREE_A1_CFG
from parkour.pair_target_progress import PairTargetProgress
from parkour.shared_terrain import scripted_pair_targets

@configclass
class ContinuousTrackerCfg(FootholdCfg):
    contact_target_mode='point'
    bound_reward_scope='all'
    pair_contact_quorum='both'
    initial_rear_target='own_stance'
    bound_reward_per_second=0.
    body_progress_weight=0.
    body_progress_reference='pair_midpoint'
    gap_jump_bonus=0.
    terminal_motion_cost=0.
    motion_control=None
    observation_space=105
    episode_length_s=12.
    action_scale=.5
    success_radius_m=.06
    contact_hold_steps=3
    final_hold_steps=10
    robot=copy.deepcopy(UNITREE_A1_CFG).replace(prim_path='/World/envs/env_.*/Robot')
    robot.spawn.articulation_props.enabled_self_collisions=True

class ContinuousTrackerEnv(FootholdEnv):
    def __init__(self,cfg,render_mode=None):
        super().__init__(cfg,render_mode)
        if self.foot_names!=['FL_foot','FR_foot','RL_foot','RR_foot']:
            raise ValueError('Unexpected asset foot order')
        self.layout=cfg.support_contract['layout']
        self.calibration=copy.deepcopy(cfg.support_contract['calibration'])
        self.nominal_xy=torch.tensor(self.calibration['foot_xy_m'],device=self.device)
        self.calibrated_root=torch.tensor(self.calibration['root_state'],device=self.device)
        self.calibrated_joint_pos=torch.tensor(self.calibration['joint_positions'],device=self.device)
        self.target_script=scripted_pair_targets(self.layout,self.calibration['foot_xy_m'],initial_rear_target=cfg.initial_rear_target)
        self.plan=torch.tensor(self.target_script['positions_m'],device=self.device)
        self.surface_rotations=torch.tensor([s['rotation_local_to_world'] for s in self.layout['surfaces']],device=self.device)
        self.surface_centers=torch.tensor([s['top_center_m'] for s in self.layout['surfaces']],device=self.device)
        self.gap_surfaces=torch.tensor([s.get('scenario_role')=='gap_landing' for s in self.layout['surfaces']],device=self.device)
        self.surface_normals=torch.tensor([s['normal'] for s in self.layout['surfaces']],device=self.device)
        self.surface_halves=torch.tensor([s['usable_half_extents_m'] for s in self.layout['surfaces']],device=self.device)
        self.surface_box_centers=torch.tensor([s['center_m'] for s in self.layout['surfaces']],device=self.device)
        self.surface_box_sizes=torch.tensor([s['size_m'] for s in self.layout['surfaces']],device=self.device)
        self.progress=PairTargetProgress(self.num_envs,len(self.layout['surfaces']),self.device,cfg.contact_hold_steps,cfg.pair_contact_quorum,cfg.initial_rear_target=='front_stance')
        self.nonfoot_ids=[i for i in range(len(self.contacts.body_names)) if i not in self.contact_ids]
        self.final_hold=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.accept_events=torch.zeros(self.num_envs,2,dtype=torch.bool,device=self.device)
        self.current_valid=torch.zeros(self.num_envs,4,dtype=torch.bool,device=self.device)
        self.current_error=torch.zeros(self.num_envs,4,device=self.device)
        self.goal=torch.tensor(self.layout['goal_position_m'],device=self.device)
        points=self.surface_centers[:,:2]
        self.map_low=points.amin(dim=0)-1.;self.map_high=points.amax(dim=0)+1.
        from parkour.flight_events import FlightEvents
        self.flights=FlightEvents(self.num_envs,self.device)
        self.travel_jumps=torch.zeros_like(self.flights.count)
        self.travel_airborne=torch.zeros_like(self.flights.count)
        self.gap_credit=None
        if cfg.gap_jump_bonus:
            from parkour.gap_jump_credit import GapJumpCredit
            if not self.layout.get('gap_locations'):raise ValueError('Gap jump credit needs explicit gaps')
            self.gap_credit=GapJumpCredit(self.num_envs,len(self.layout['surfaces']),self.layout['gap_locations'],self.device)
        self.new_gap_credit=torch.zeros(self.num_envs,device=self.device)
        self.active_motion_steps=torch.zeros(self.num_envs,dtype=torch.long,device=self.device)
        self.travel_motion_steps=torch.zeros_like(self.active_motion_steps)
        original_update=self.scene.update
        def update(dt):
            original_update(dt)
            if dt<=0:return
            self.active_motion_steps+=(self.robot.data.root_lin_vel_w.norm(dim=1)>.15)
            self.travel_motion_steps+=(self.robot.data.root_lin_vel_w.norm(dim=1)>.15)&~(self.progress.target==self.progress.target_count-1).all(dim=1)
            was_air=self.flights.air.clone() if self.gap_credit is not None else None
            previous_airborne=self.flights.airborne_count.clone()
            valid_flight=self.flights.update(self.contacts.data.net_forces_w[:,self.contact_ids],self.robot.data.root_pos_w[:,2],
                self.robot.data.root_lin_vel_w[:,2],self.contacts.data.net_forces_w[:,self.nonfoot_ids].norm(dim=-1).amax(dim=1),dt)
            traveling=~(self.progress.target==self.progress.target_count-1).all(dim=1)
            self.travel_jumps+=valid_flight&traveling
            self.travel_airborne+=(self.flights.airborne_count-previous_airborne)*traveling
            if self.gap_credit is not None:
                self.gap_credit.observe(self.flights.air&~was_air,valid_flight,
                    self.robot.data.root_pos_w[:,:2]-self.scene.env_origins[:,:2],self.progress.target)
        self.scene.update=update
        self.body_progress_before=torch.zeros(self.num_envs,3,device=self.device)
        self.body_waypoint=torch.zeros_like(self.body_progress_before)
        self.stance_offset=self.calibrated_root[:3]-torch.cat([self.nominal_xy,torch.full((4,1),.02,device=self.device)],dim=1).mean(dim=0)
        self._sync_targets()
    def _pre_physics_step(self,actions):
        if self.cfg.motion_control is not None:
            from parkour.motion_control import limit_reference
            actions=limit_reference(actions.clamp(-self.cfg.action_limit,self.cfg.action_limit),self.actions,
                self.cfg.action_scale,self.step_dt,self.cfg.motion_control['joint_reference_rate_rad_s'])
        super()._pre_physics_step(actions)
        if self.cfg.body_progress_weight:
            from parkour.body_progress import waypoint
            self.body_progress_before.copy_(self.robot.data.root_pos_w)
            self.body_waypoint.copy_(waypoint(self.targets,self.stance_offset))
            if self.cfg.body_progress_reference=='gap_landing':
                from parkour.body_progress import gap_landing_waypoint
                self.body_waypoint.copy_(gap_landing_waypoint(self.targets,self.stance_offset,
                    self.progress.target[:,0],self.progress.accepted[:,0],self.gap_surfaces,
                    self.surface_centers,self.scene.env_origins,self.calibrated_root[2]))
    def _sync_targets(self):
        pair=torch.arange(2,device=self.device)[None,:].expand(self.num_envs,-1)
        self.targets=self.plan[pair,self.progress.target].reshape(self.num_envs,4,3)+self.scene.env_origins[:,None,:]
    def _reset_idx(self,ids):
        if ids is None:ids=self.robot._ALL_INDICES
        super()._reset_idx(ids)
        self.progress.reset(ids);self.flights.reset(ids);self.final_hold[ids]=0;self.accept_events[ids]=False
        self.active_motion_steps[ids]=0
        self.travel_motion_steps[ids]=0
        self.travel_jumps[ids]=0;self.travel_airborne[ids]=0
        self.new_gap_credit[ids]=0
        if self.gap_credit is not None:self.gap_credit.reset(ids,self.calibrated_root[:2].expand(len(ids),-1))
        self.current_valid[ids]=False;self.current_error[ids]=0
        root=self.calibrated_root.expand(len(ids),-1).clone();root[:,:3]+=self.scene.env_origins[ids]
        self.robot.write_root_pose_to_sim(root[:,:7],ids);self.robot.write_root_velocity_to_sim(root[:,7:],ids)
        q=self.calibrated_joint_pos.expand(len(ids),-1).clone()
        self.robot.write_joint_state_to_sim(q,torch.zeros_like(q),env_ids=ids)
        self._sync_targets()
    def _get_observations(self):
        self._sync_targets()
        indices,mask=self.progress.lookahead()
        pair=torch.arange(2,device=self.device)[None,:,None].expand(self.num_envs,2,2)
        # N, pair, horizon, left/right, XYZ -> N, foot, horizon, XYZ.
        points=self.plan[pair,indices].permute(0,1,3,2,4).reshape(self.num_envs,4,2,3)
        normals=self.surface_normals[indices][:,:,None,:,:].expand(-1,-1,2,-1,-1).reshape(self.num_envs,4,2,3)
        q=self.robot.data.root_quat_w[:,None,None,:].expand(-1,4,2,-1).reshape(-1,4)
        relative=points+self.scene.env_origins[:,None,None,:]-self.robot.data.root_pos_w[:,None,None,:]
        target_b=quat_apply_inverse(q,relative.reshape(-1,3)).reshape(self.num_envs,4,2,3)
        normal_b=quat_apply_inverse(q,normals.reshape(-1,3)).reshape(self.num_envs,4,2,3)
        foot_mask=mask[:,:,None,:].expand(-1,-1,2,-1).reshape(self.num_envs,4,2,1)
        target_b*=foot_mask;normal_b*=foot_mask
        proprio=torch.cat([self.robot.data.root_lin_vel_b,self.robot.data.root_ang_vel_b,self.robot.data.projected_gravity_b,
            self.robot.data.joint_pos-self.robot.data.default_joint_pos,self.robot.data.joint_vel*.05,self.actions],dim=1)
        obs=torch.cat([proprio,target_b.flatten(1),normal_b.flatten(1),(self.progress.age*self.step_dt).clamp_max(2.),
            mask.flatten(1).float(),(self.progress.target==self.progress.target_count-1).float(),self.contact_on.float()],dim=1)
        assert obs.shape==(self.num_envs,105)
        return {'policy':obs}
    def _get_dones(self):
        indices=self.progress.target.repeat_interleave(2,dim=1)
        foot=self.robot.data.body_pos_w[:,self.foot_ids]-self.scene.env_origins[:,None,:]
        R=self.surface_rotations[indices];delta=foot-self.surface_centers[indices]
        local=torch.einsum('nfji,nfj->nfi',R,delta)
        forces=self.contacts.data.net_forces_w[:,self.contact_ids]
        norm_force=(forces*self.surface_normals[indices]).sum(dim=2)
        magnitude=forces.norm(dim=2)
        self.contact_on=torch.where(self.contact_on,magnitude>2,magnitude>5)
        self.current_error=(self.robot.data.body_pos_w[:,self.foot_ids]-self.targets).norm(dim=2)
        inside=(local[:,:,:2].abs()<=self.surface_halves[indices]).all(dim=2)&(local[:,:,2]>=0)&(local[:,:,2]<=.04)
        self.current_valid=inside&(norm_force>5)&(self.current_error<=self.cfg.success_radius_m)
        if self.cfg.contact_target_mode=='surface_region':
            from parkour.surface_region import exposed_projection
            exposed=exposed_projection(foot,indices,self.surface_rotations,self.surface_centers,self.surface_box_centers,self.surface_box_sizes)
            self.current_valid=inside&(norm_force>5)&exposed
        decision=self.progress.update(self.current_valid);self.accept_events=decision['accepted_now']
        nonfoot=self.contacts.data.net_forces_w_history[:,:,self.nonfoot_ids].norm(dim=-1).amax(dim=(1,2))>5
        root=self.robot.data.root_pos_w-self.scene.env_origins
        outside=((root[:,:2]<self.map_low)|(root[:,:2]>self.map_high)).any(dim=1)
        self.failure_nonfoot=nonfoot
        self.failure_outside=outside
        self.failure_low=root[:,2]<self.layout['catch_floor_z_m']+.13
        self.failure_tilt=self.robot.data.projected_gravity_b[:,2]>-math.cos(math.radians(100))
        peaks=self.contacts.data.net_forces_w_history[:,:,self.nonfoot_ids].norm(dim=-1).amax(dim=1)
        self.failure_nonfoot_id=torch.tensor(self.nonfoot_ids,device=self.device)[peaks.argmax(dim=1)]
        self.failure=nonfoot|outside|self.failure_low|self.failure_tilt
        if self.gap_credit is not None:self.new_gap_credit=self.gap_credit.settle(self.progress.accepted,self.failure)
        final=decision['sequence_completed']&self.current_valid.all(dim=1)&((root[:,:2]-self.goal[:2]).norm(dim=1)<.3)&(self.robot.data.root_lin_vel_b.norm(dim=1)<.2)&(self.robot.data.root_ang_vel_b.norm(dim=1)<1.)
        self.final_hold=torch.where(final,self.final_hold+1,0)
        self.success=(self.final_hold>=self.cfg.final_hold_steps)&~self.failure
        term=self.success|self.failure
        return term,(self.episode_length_buf>=self.max_episode_length)&~term
    def _get_rewards(self):
        # First baseline: contact progress, shaping, actuator/action costs. No mid-course stop reward.
        dense=2.*(torch.exp(-self.current_error/.25).mean(dim=1)-1.)-.1
        if self.cfg.bound_reward_per_second:
            from parkour.bounding_style import bounding_mask
            terminal=(self.progress.target==self.progress.target_count-1).all(dim=1) if self.cfg.bound_reward_scope=='travel_only' else None
            dense+=self.cfg.bound_reward_per_second*bounding_mask(self.contact_on,terminal)
        dense-=.0001*self.robot.data.applied_torque.square().sum(dim=1)
        dense-=.01*(self.actions-self.previous_actions).square().sum(dim=1)
        if self.cfg.terminal_motion_cost:
            final_targets=(self.progress.target==self.progress.target_count-1).all(dim=1)
            motion=self.robot.data.root_lin_vel_b.square().sum(dim=1)+.1*self.robot.data.root_ang_vel_b.square().sum(dim=1)
            dense-=self.cfg.terminal_motion_cost*motion*final_targets
        if self.cfg.motion_control is not None:
            spec=self.cfg.motion_control
            terminal=(self.progress.target==self.progress.target_count-1).all(dim=1)
            target=(~terminal)*spec['target_speed_mps']
            speed=self.robot.data.root_lin_vel_w[:,:2].norm(dim=1)
            dense-=spec['speed_cost']*(speed-target).square()
            dense-=spec['joint_speed_cost']*(self.robot.data.joint_vel.abs()-spec['joint_speed_soft_rad_s']).clamp_min(0).square().sum(dim=1)
        reward=dense*self.step_dt+2.*self.accept_events.sum(dim=1)+5.*self.success-5.*self.failure
        reward+=self.cfg.gap_jump_bonus*self.new_gap_credit
        if self.cfg.body_progress_weight:
            from parkour.body_progress import progress_reward
            reward+=progress_reward(self.body_progress_before,self.robot.data.root_pos_w,self.body_waypoint,self.cfg.body_progress_weight)
        self.error_sum+=self.current_error.mean(dim=1);self.sample_count+=1;self.reward_sum+=reward
        self.extras['terminal_metrics']={'success':self.success.clone(),'failure':self.failure.clone(),'timeout':self.reset_time_outs.clone(),
            'length':self.episode_length_buf.clone(),'mean_error_m':(self.error_sum/self.sample_count.clamp_min(1)).clone(),
            'final_error_m':self.current_error.mean(dim=1).clone(),'return':self.reward_sum.clone(),
            'front_accepted_index':self.progress.accepted[:,0].clone(),'rear_accepted_index':self.progress.accepted[:,1].clone(),
            'front_target_index':self.progress.target[:,0].clone(),'rear_target_index':self.progress.target[:,1].clone(),
            'final_hold_steps':self.final_hold.clone(),'measured_jump_count':self.flights.count.clone(),
            'clean_airborne_count':self.flights.airborne_count.clone(),
            'travel_measured_jump_count':self.travel_jumps.clone(),'travel_clean_airborne_count':self.travel_airborne.clone(),
            'active_motion_seconds':self.active_motion_steps*self.physics_dt,
            'travel_motion_seconds':self.travel_motion_steps*self.physics_dt,
            'completed_surface_transfers':self.progress.accepted.amin(dim=1).clamp_min(0).clone(),
            'failure_nonfoot':self.failure_nonfoot.clone(),'failure_nonfoot_body_id':self.failure_nonfoot_id.clone(),
            'failure_outside_map':self.failure_outside.clone(),'failure_low_body':self.failure_low.clone(),'failure_tilt':self.failure_tilt.clone()}
        if self.gap_credit is not None:self.extras['terminal_metrics']['credited_gap_jumps']=self.gap_credit.paid.sum(dim=1).clone()
        return reward
