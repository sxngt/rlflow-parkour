"""One bounded Gaussian definition shared by PPO rollout and update."""
import math
import torch
from torch.distributions import Normal
from rsl_rl.modules import ActorCritic


def cap_for_update(config, update):
    spec=config.get('exploration')
    if spec is None:return None
    if type(update) is not int or update<0:raise ValueError('Invalid update')
    if spec.get('kind') not in ('bounded_gaussian_v1','bounded_mean_gaussian_v2'):raise ValueError('Unknown exploration contract')
    lower=spec['min_std'];stages=spec['stages']
    if not math.isfinite(lower) or lower<=0 or not stages:raise ValueError('Invalid std floor/stages')
    previous=-1;last=float('inf');active=None
    for stage in stages:
        step,value=stage['start_update'],stage['max_std']
        if type(step) is not int or step<=previous or step<0:raise ValueError('Stages must increase')
        if not math.isfinite(value) or value<lower or value>last:raise ValueError('Invalid std cap')
        if step<=update:active=value
        previous,last=step,value
    if stages[0]['start_update']!=0:raise ValueError('Schedule must start at zero')
    return active


class BoundedActorCritic(ActorCritic):
    def __init__(self,*args,min_std,max_std,bounded_mean=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.bounded_mean=bounded_mean
        if self.noise_std_type!='scalar':raise ValueError('Bounded policy requires scalar std parameter')
        self.register_buffer('std_floor',torch.tensor(float(min_std)))
        self.register_buffer('std_cap',torch.tensor(float(max_std)))

    def update_distribution(self,observations):
        mean=self.act_inference(observations)
        std=self.std.clamp(min=self.std_floor,max=self.std_cap).expand_as(mean)
        self.distribution=Normal(mean,std)

    def act_inference(self,observations):
        mean=self.actor(observations)
        return mean.tanh() if self.bounded_mean else mean
