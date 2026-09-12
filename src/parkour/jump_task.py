"""P2 flat-ground commanded jump. New contact/flight contract, not P1 replay."""
import copy
import torch
from isaaclab.utils import configclass
from isaaclab_assets import UNITREE_A1_CFG
from parkour.task import FootholdCfg,FootholdEnv
from parkour.sequential_task import SequentialCfg,SequentialEnv
from parkour.jump_events import jump_transition,apex_progress,landing_height_cost,landing_settle_cost
from parkour.landing_precision import precision_reward

@configclass
class JumpCfg(SequentialCfg):
    observation_space=66
    episode_length_s=4.
    robot=copy.deepcopy(UNITREE_A1_CFG).replace(prim_path='/World/envs/env_.*/Robot')
    robot.spawn.articulation_props.enabled_self_collisions=True
    jump={}
    observation_history=None

class JumpEnv(SequentialEnv):
    contact_group_all=True
    phase_labels={0:'도약 준비',1:'비행',2:'착지·안정화'}
    def __init__(self,cfg,render_mode=None):
        super().__init__(cfg,render_mode)
        self.jump=cfg.jump
        if self.jump.get('landing_precision_mode', 'mean') not in ('mean', 'worst_after_landing_v1'):
            raise ValueError('Unknown landing precision aggregation')
        self.nonfoot_ids=[i for i in range(len(self.contacts.body_names)) if i not in self.contact_ids]
        self.flight_seen=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        self.landed=torch.zeros_like(self.flight_seen)
        self.touched=torch.zeros(self.num_envs,4,dtype=torch.bool,device=self.device)
        self.apex=torch.zeros(self.num_envs,device=self.device)
        self.air_time=torch.zeros_like(self.apex)
        self.apex_progress=torch.zeros_like(self.apex)
        self.apex_progress_delta=torch.zeros_like(self.apex)
        self.required_apex=torch.zeros_like(self.apex)
        self.flight_event=torch.zeros_like(self.flight_seen)
        self.new_touch=torch.zeros_like(self.touched)

    def active_feet(self):
        return torch.full_like(self.stage,-1)  # all-four group, no single active foot

    def set_sequence_offsets(self,offsets,env_ids=None,episode_orders=None):
        super().set_sequence_offsets(offsets,env_ids,episode_orders)
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        self.targets[env_ids]=self.landing_goals[env_ids]

    def _reset_idx(self,env_ids):
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        for x in [self.flight_seen,self.landed,self.touched,self.apex,self.air_time,self.flight_event,self.new_touch,self.apex_progress,self.apex_progress_delta]:x[env_ids]=0
        low,high=self.jump['apex_range_m']
        self.required_apex[env_ids]=low+(high-low)*torch.rand(len(env_ids),device=self.device,generator=self.generator)
        offset=torch.zeros(len(env_ids),4,2,device=self.device)
        self.set_sequence_offsets(offset,env_ids)
        if hasattr(self, "observation_history_buffer"):
            self.observation_history_buffer.reset(env_ids)

    def maneuver_time_s(self):
        """Local maneuver clock; single-jump episodes retain their original clock."""
        return self.episode_length_buf*self.step_dt

    def _pre_physics_step(self,actions):
        super()._pre_physics_step(actions)
        self.actions[self.maneuver_time_s()<self.jump['settle_seconds']]=0

    def launch_rise_m(self):
        rise=self.robot.data.root_pos_w[:,2]-self.scene.env_origins[:,2]-self.calibrated_root[2]
        if hasattr(self, 'planned_support_heights'):
            heights=torch.tensor(self.planned_support_heights,device=self.device)
            rise=rise-heights[self.chain.completed]
        return rise

    def landing_height_error_m(self, segment=None):
        error=self.robot.data.root_pos_w[:,2]-self.scene.env_origins[:,2]-self.calibrated_root[2]
        if hasattr(self, 'planned_support_heights'):
            heights=torch.tensor(self.planned_support_heights,device=self.device)
            error=error-heights[(self.chain.completed if segment is None else segment)+1]
        return error

    def _get_observations(self):
        base=FootholdEnv._get_observations(self)['policy']
        rise=self.launch_rise_m()
        clock=(self.maneuver_time_s()/self.jump['settle_seconds']).clamp_max(1)
        observation=torch.cat([base,torch.nn.functional.one_hot(self.phase,3),
            (self.required_apex-rise)[:,None],clock[:,None]],dim=1)
        if self.cfg.observation_history is not None:
            if not hasattr(self, 'observation_history_buffer'):
                from parkour.observation_history import ObservationHistory
                self.observation_history_buffer=ObservationHistory(self.num_envs,self.device,self.cfg.observation_history)
            observation=self.observation_history_buffer.encode(observation,self.episode_length_buf)
        return {'policy':observation}

    def _get_dones(self):
        spec=self.jump
        history=self.contacts.data.net_forces_w_history.norm(dim=-1)
        feet_history=history[:,:,self.contact_ids]
        force=self.contacts.data.net_forces_w[:,self.contact_ids].norm(dim=-1)
        self.contact_on=torch.where(self.contact_on,force>2,force>5)
        self.nonfoot_collision=history[:,:,self.nonfoot_ids].amax(dim=(1,2))>5
        height=self.robot.data.root_pos_w[:,2]-self.scene.env_origins[:,2]
        rise=self.launch_rise_m()
        landing_error=self.landing_height_error_m()
        vz=self.robot.data.root_lin_vel_w[:,2]
        settled=self.maneuver_time_s()>=spec['settle_seconds']
        air_samples=(feet_history<2).all(dim=2)
        air_window=air_samples.all(dim=1)
        supported=(feet_history>2).all(dim=(1,2))
        self.air_time+=air_samples.sum(dim=1)*self.physics_dt*settled
        root_xy = self.robot.data.root_pos_w[:,:2]-self.scene.env_origins[:,:2]
        bounds = getattr(self, 'course_root_bounds', None)
        outside = root_xy.norm(dim=1)>.6 if bounds is None else (
            (root_xy[:,0]<bounds[0]) | (root_xy[:,0]>bounds[1]) |
            (root_xy[:,1]<bounds[2]) | (root_xy[:,1]>bounds[3]))
        self.failure=self.nonfoot_collision|(height<.13)|(self.robot.data.projected_gravity_b[:,2]>-.5)|outside
        # Only post-confirmation, pre-touch flight heights qualify for apex success.
        self.apex=torch.where(self.flight_seen&~self.landed&air_window,torch.maximum(self.apex,rise),self.apex)
        values=jump_transition(self.flight_seen,self.landed,self.touched,self.contact_on,air_window,settled,rise,vz,
            self._errors(),self.apex,self.required_apex,self.robot.data.root_ang_vel_b.norm(dim=1),landing_error,supported,
            self.failure,self.hold_steps,self.step_dt,spec)
        self.flight_seen,self.landed,self.touched,self.hold_steps,self.flight_event,self.new_touch,self.success=values
        self.apex=torch.where(self.flight_event,torch.maximum(self.apex,rise),self.apex)
        self.apex_progress,self.apex_progress_delta=apex_progress(self.apex,self.required_apex,spec['flight_min_rise_m'],self.apex_progress)
        self.phase=torch.where(self.landed,2,torch.where(self.flight_seen,1,0))
        self.stage=self.phase.clone()
        term=self.success|self.failure
        return term,(self.episode_length_buf>=self.max_episode_length)&~term

    def _get_rewards(self):
        settled=self.maneuver_time_s()>=self.jump['settle_seconds']
        errors=self._errors()
        launch=2*self.robot.data.root_lin_vel_w[:,2].clamp(0,1.5)
        precision=precision_reward(errors,self.landed,self.jump.get('landing_precision_mode','mean'))
        dense=torch.where(self.flight_seen,precision,launch)*settled-.1
        dense-=.5*self.robot.data.projected_gravity_b[:,:2].square().sum(dim=1)
        dense-=.02*self.robot.data.root_ang_vel_b.square().sum(dim=1)
        dense-=.002*(self.actions-self.previous_actions).square().sum(dim=1)
        dense-=.00002*self.robot.data.applied_torque.square().sum(dim=1)
        rise=self.landing_height_error_m(getattr(self, "segment_before", None))
        dense-=self.jump.get('landing_height_weight',0)*landing_height_cost(rise,self.landed,self.jump['final_height_error_max_m'])
        dense-=landing_settle_cost(self.robot.data.root_lin_vel_w[:,2],self.contact_on,self.landed,
            self.jump.get('landing_vz_weight',0),self.jump.get('landing_support_weight',0))
        reward=dense*self.step_dt+3*self.flight_event.float()+self.new_touch.sum(dim=1)+8*self.success.float()-10*self.failure.float()
        reward+=self.jump.get('apex_progress_weight',0)*self.apex_progress_delta*(~self.failure)
        if getattr(self, 'record_reward_components', False):
            self.extras['reward_components'] = {
                'dense': (dense*self.step_dt).clone(),
                'flight_event': (3*self.flight_event.float()).clone(),
                'contact_event': self.new_touch.sum(dim=1).clone(),
                'success': (8*self.success.float()).clone(),
                'failure': (-10*self.failure.float()).clone(),
                'apex_progress': (self.jump.get('apex_progress_weight',0)*self.apex_progress_delta*(~self.failure)).clone(),
            }
        error=errors.mean(dim=1);self.error_sum+=error;self.sample_count+=1;self.reward_sum+=reward
        self.extras['terminal_metrics']={'success':self.success.clone(),'failure':self.failure.clone(),'timeout':self.reset_time_outs.clone(),
          'length':self.episode_length_buf.clone(),'mean_error_m':(self.error_sum/self.sample_count.clamp_min(1)).clone(),
          'final_error_m':error.clone(),'return':self.reward_sum.clone(),'completed_contacts':self.touched.sum(dim=1).clone(),
          'valid_flight':self.flight_seen.clone(),'landed':self.landed.clone(),'flight_apex_rise_m':self.apex.clone(),
          'required_apex_m':self.required_apex.clone(),'air_time_s':self.air_time.clone(),
          'nonfoot_collision':self.nonfoot_collision.clone(),'final_stable_steps':self.hold_steps.clone(),
          'final_height_error_m':rise.clone(),'final_vz_m_s':self.robot.data.root_lin_vel_w[:,2].clone(),
          'final_angular_speed_rad_s':self.robot.data.root_ang_vel_b.norm(dim=1).clone(),
          'final_contact_all':self.contact_on.all(dim=1).clone(),
          'final_all_feet_in_radius':(errors<=self.jump['landing_radius_m']).all(dim=1).clone(),
          'final_supported':(self.contacts.data.net_forces_w_history.norm(dim=-1)[:,:,self.contact_ids]>2).all(dim=(1,2)).clone()}
        return reward
