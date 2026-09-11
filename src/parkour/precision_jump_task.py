"""P2 first landing precision: later foot corrections cannot repair first contact."""
import torch
from parkour.jump_task import JumpEnv
from parkour.first_touch import FirstTouch

class PrecisionJumpEnv(JumpEnv):
    def __init__(self,cfg,render_mode=None):
        super().__init__(cfg,render_mode)
        self.first_touch=FirstTouch(self.num_envs,self.device)
        self.first_touch_bonus=torch.zeros(self.num_envs,device=self.device)
        self.stabilized=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        self.original_scene_update=self.scene.update
        def update(dt):
            self.original_scene_update(dt)
            if dt<=0:return
            origin=self.scene.env_origins[:,None,:2]
            new=self.first_touch.update(self.flight_seen,self.contacts.data.net_forces_w[:,self.contact_ids],
                self.robot.data.body_pos_w[:,self.foot_ids,:2]-origin,self.targets[:,:,:2]-origin)
            self.first_touch_bonus+=(new*torch.exp(-self.first_touch.errors/self.jump['first_touch_reward_scale_m'])).sum(dim=1)*self.jump['first_touch_reward_weight']
        self.scene.update=update

    def _reset_idx(self,env_ids):
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        self.first_touch.reset(env_ids);self.first_touch_bonus[env_ids]=0;self.stabilized[env_ids]=False

    def _pre_physics_step(self,actions):
        super()._pre_physics_step(actions)
        self.first_touch_bonus.zero_()

    def _get_dones(self):
        super()._get_dones()
        self.stabilized|=self.success
        self.success&=self.first_touch.within(self.jump['landing_radius_m'])
        term=self.success|self.failure
        return term,(self.episode_length_buf>=self.max_episode_length)&~term

    def _get_rewards(self):
        reward=super()._get_rewards()
        extra=self.first_touch_bonus*(~self.failure)
        reward+=extra;self.reward_sum+=extra
        metrics=self.extras['terminal_metrics']
        metrics['return']=self.reward_sum.clone()
        metrics['stabilized_once']=self.stabilized.clone()
        metrics['first_touch_all_within']=self.first_touch.within(self.jump['landing_radius_m']).clone()
        metrics['first_touch_count']=self.first_touch.seen.sum(dim=1).clone()
        for i,name in enumerate(['fl','fr','rl','rr']):
            metrics[f'first_touch_error_{name}_m']=torch.where(self.first_touch.seen[:,i],self.first_touch.errors[:,i],-1.).clone()
        return reward
