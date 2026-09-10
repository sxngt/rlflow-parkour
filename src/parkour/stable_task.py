"""P1 step 02: three-support event checks and a distinct final stabilization stage."""
import math
import torch
from parkour.sequential_task import SequentialEnv


from parkour.sequence import stable_landing


class StableSequentialEnv(SequentialEnv):
    def __init__(self,cfg,render_mode=None):
        super().__init__(cfg,render_mode)
        self.stable_steps=torch.zeros_like(self.stage)
        self.quality_sum=torch.zeros(self.num_envs,device=self.device)

    def _reset_idx(self,env_ids):
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        self.stable_steps[env_ids]=0
        self.quality_sum[env_ids]=0

    def _get_dones(self):
        super()._get_dones()
        final=self.stage==4
        self.lift_event &= ~final
        self.place_event &= ~final
        spec=self.seq['stability']
        height=self.robot.data.root_pos_w[:,2]-self.scene.env_origins[:,2]
        stable=stable_landing(self.stage,self.contact_on,self._errors(),self.robot.data.root_lin_vel_w[:,2],
            self.robot.data.root_ang_vel_b.norm(dim=1),height-self.calibrated_root[2],self.cfg.success_radius_m,spec)
        self.stable_steps=torch.where(stable,self.stable_steps+1,0)
        self.success=(self.stable_steps>=math.ceil(spec['final_hold_seconds']/self.step_dt)) & ~self.failure
        terminated=self.success|self.failure
        return terminated,(self.episode_length_buf>=self.max_episode_length)&~terminated

    def _get_rewards(self):
        active=self.order[self.stage.clamp_max(3)]
        desired=self.targets.clone()
        desired[self.indices,active,2]+=((self.phase==0)&(self.stage<4))*self.seq['lift_target_height_m']
        errors=(self.robot.data.body_pos_w[:,self.foot_ids]-desired).norm(dim=-1)
        active_error=errors[self.indices,active]
        support_error=(errors.sum(dim=1)-active_error)/3
        precision=torch.exp(-(active_error/.05).square())
        dense=(precision-1-(support_error/.06).square().clamp_max(1)
               -self.robot.data.projected_gravity_b[:,:2].square().sum(dim=1)
               -.02*self.robot.data.root_ang_vel_b.square().sum(dim=1)
               -.002*(self.actions-self.previous_actions).square().sum(dim=1)
               -.00002*self.robot.data.applied_torque.square().sum(dim=1))
        vz2=self.robot.data.root_lin_vel_w[:,2].square()
        dense-=self.seq['stability']['vertical_velocity_penalty']*vz2
        reward=(dense*self.step_dt+self.lift_event.float()+3*self.place_event.float()
                +5*self.success.float()-30*self.failure.float())
        planar=self._errors().mean(dim=1)
        self.error_sum+=planar;self.sample_count+=1;self.reward_sum+=reward;self.quality_sum+=vz2
        self.extras['terminal_metrics']={
            'success':self.success.clone(),'failure':self.failure.clone(),'timeout':self.reset_time_outs.clone(),
            'length':self.episode_length_buf.clone(),'mean_error_m':(self.error_sum/self.sample_count.clamp_min(1)).clone(),
            'final_error_m':planar.clone(),'return':self.reward_sum.clone(),
            'completed_contacts':(self.stage+self.place_event.long()).clamp_max(4).clone(),
            'mean_squared_vertical_speed':(self.quality_sum/self.sample_count.clamp_min(1)).clone(),
            'final_stable_steps':self.stable_steps.clone()}
        lift=self.lift_event&~self.reset_buf
        self.phase[lift]=1;self.hold_steps[lift]=0
        ids=(self.place_event&~self.reset_buf).nonzero().flatten()
        self.stage[ids]+=1
        self.phase[ids]=torch.where(self.stage[ids]==4,1,0)
        self.grounded_seen[ids]=False;self.lift_count[ids]=0;self.hold_steps[ids]=0
        moving=ids[self.stage[ids]<4]
        next_feet=self.order[self.stage[moving]]
        self.targets[moving,next_feet]=self.landing_goals[moving,next_feet]
        return reward
