"""Flat forward jump with a fixed launch region and measured airborne travel."""
import torch
from parkour.jump_sampling import sample_distances
from parkour.precision_jump_task import PrecisionJumpEnv
from parkour.flight_travel import FlightTravel,TravelLandingReward

class DirectedJumpEnv(PrecisionJumpEnv):
    def __init__(self,cfg,render_mode=None):
        super().__init__(cfg,render_mode)
        self.travel=FlightTravel(self.num_envs,self.device)
        self.travel_reward=TravelLandingReward(self.num_envs,self.device,self.jump.get('travel_reward_mode','distance_only'))
        self.goal_distance=torch.zeros(self.num_envs,device=self.device)
        self.precise_stabilized=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
        interval=self.jump.get('train_forward_range_m')
        self.goal_sample_values=self.jump.get('train_forward_choices_m', [interval[0]] if interval and interval[0]==interval[1] else [])
        self.goal_draw_counts=torch.zeros(len(self.goal_sample_values),dtype=torch.long,device=self.device)
    def set_sequence_offsets(self,offsets,env_ids=None,episode_orders=None):
        super().set_sequence_offsets(offsets,env_ids,episode_orders)
        if hasattr(self,'goal_distance'):
            if env_ids is None:env_ids=self.robot._ALL_INDICES
            self.goal_distance[env_ids]=offsets[:,0,0]
    def _reset_idx(self,env_ids):
        if env_ids is None:env_ids=self.robot._ALL_INDICES
        super()._reset_idx(env_ids)
        self.travel.reset(env_ids);self.precise_stabilized[env_ids]=False
        self.travel_reward.reset(env_ids)
        distance=sample_distances(self.jump,len(env_ids),self.device,self.generator)
        for i,value in enumerate(self.goal_sample_values):
            self.goal_draw_counts[i]+=(torch.abs(distance-value)<1e-7).sum()
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
        extra=self.travel_reward.collect(self.travel,self.goal_distance,self.failure,
            self.jump.get('travel_reward_weight',0.),self.jump.get('travel_reward_scale_m',.03),
            self.first_touch,self.jump.get('travel_precision_scale_m'))
        reward+=extra;self.reward_sum+=extra;m['return']=self.reward_sum.clone()
        m['first_travel_reward']=extra.clone()
        m.update(goal_forward_m=self.goal_distance.clone(),launch_recorded=self.travel.launched.clone(),
            launch_in_region=self.travel.launch_ok.clone(),flight_touch_recorded=self.travel.touched.clone(),
            flight_forward_m=torch.where(self.travel.touched,self.travel.distance(),-1.).clone(),travel_requirement_met=self.travel.valid(self.goal_distance,self.jump['travel_tolerance_m']).clone(),
            distance_requirement_met=self.travel.distance_met(self.goal_distance,self.jump['travel_tolerance_m']).clone(),
            precise_stabilized_once=self.precise_stabilized.clone())
        for axis,i in [('x',0),('y',1)]:
            m[f'launch_root_{axis}_m']=self.travel.launch_xy[:,i].clone()
            m[f'first_touch_root_{axis}_m']=self.travel.touch_xy[:,i].clone()
        return reward
