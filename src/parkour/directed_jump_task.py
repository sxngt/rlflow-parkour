"""Flat forward jump with a fixed launch region and measured airborne travel."""
import torch
from parkour.precision_jump_task import PrecisionJumpEnv
from parkour.flight_travel import FlightTravel

class DirectedJumpEnv(PrecisionJumpEnv):
    def __init__(self,cfg,render_mode=None):
        super().__init__(cfg,render_mode)
        self.travel=FlightTravel(self.num_envs,self.device)
        self.goal_distance=torch.zeros(self.num_envs,device=self.device)
        self.precise_stabilized=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
    def set_sequence_offsets(self,offsets,env_ids=None,episode_orders=None):
        super().set_sequence_offsets(offsets,env_ids,episode_orders)
        if hasattr(self,'goal_distance'):
            if env_ids is None:env_ids=self.robot._ALL_INDICES
            self.goal_distance[env_ids]=offsets[:,0,0]
    def _reset_idx(self,env_ids):
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        self.travel.reset(env_ids);self.precise_stabilized[env_ids]=False
        low,high=self.jump['train_forward_range_m']
        distance=low+(high-low)*torch.rand(len(env_ids),device=self.device,generator=self.generator)
        offsets=torch.zeros(len(env_ids),4,2,device=self.device);offsets[:,:,0]=distance[:,None]
        self.set_sequence_offsets(offsets,env_ids)
    def on_first_physics_contact(self,new):
        self.travel.touch(new.any(dim=1),self.robot.data.root_pos_w[:,:2]-self.scene.env_origins[:,:2])
    def _get_dones(self):
        super()._get_dones()
        self.travel.launch(self.flight_event,self.robot.data.root_pos_w[:,:2]-self.scene.env_origins[:,:2],
            self.calibrated_root[:2],self.jump['launch_radius_m'])
        self.precise_stabilized|=self.success
        self.failure|=self.flight_event&~self.travel.launch_ok
        self.success&=self.travel.valid(self.goal_distance,self.jump['travel_tolerance_m'])&~self.failure
        term=self.success|self.failure
        return term,(self.episode_length_buf>=self.max_episode_length)&~term
    def _get_rewards(self):
        reward=super()._get_rewards();m=self.extras['terminal_metrics']
        m.update(goal_forward_m=self.goal_distance.clone(),launch_recorded=self.travel.launched.clone(),
            launch_in_region=self.travel.launch_ok.clone(),flight_touch_recorded=self.travel.touched.clone(),
            flight_forward_m=torch.where(self.travel.touched,self.travel.distance(),-1.).clone(),travel_requirement_met=self.travel.valid(self.goal_distance,self.jump['travel_tolerance_m']).clone(),
            precise_stabilized_once=self.precise_stabilized.clone())
        for axis,i in [('x',0),('y',1)]:
            m[f'launch_root_{axis}_m']=self.travel.launch_xy[:,i].clone()
            m[f'first_touch_root_{axis}_m']=self.travel.touch_xy[:,i].clone()
        return reward
