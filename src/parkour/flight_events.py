"""Count observed takeoff/flight/landing events without enforcing a gait."""
import torch
class FlightEvents:
    def __init__(self,count,device):
        self.air=torch.zeros(count,dtype=torch.bool,device=device)
        self.duration=torch.zeros(count,device=device);self.start_z=torch.zeros_like(self.duration);self.peak_z=torch.zeros_like(self.duration)
        self.up=torch.zeros_like(self.air);self.bad=torch.zeros_like(self.air);self.had_support=torch.zeros_like(self.air)
        self.previous_z=torch.zeros_like(self.duration);self.count=torch.zeros(count,dtype=torch.long,device=device)
    def reset(self,ids):
        for value in (self.air,self.duration,self.start_z,self.peak_z,self.up,self.bad,self.had_support,self.previous_z,self.count):value[ids]=0
    def update(self,force,root_z,root_vz,nonfoot_force,dt):
        supported=(force.norm(dim=-1)>2).any(dim=1)
        start=(~supported)&(~self.air)&self.had_support
        self.air|=start
        self.start_z=torch.where(start,self.previous_z,self.start_z)
        self.peak_z=torch.where(start,root_z,self.peak_z)
        self.duration=torch.where(start,torch.zeros_like(self.duration),self.duration)
        self.up=torch.where(start,torch.zeros_like(self.up),self.up);self.bad=torch.where(start,torch.zeros_like(self.bad),self.bad)
        self.duration+=self.air*(~supported)*dt
        self.peak_z=torch.where(self.air,torch.maximum(self.peak_z,root_z),self.peak_z)
        self.up|=self.air&(root_vz>.2);self.bad|=self.air&(nonfoot_force>5)
        landed=self.air&supported
        valid=landed&(self.duration>=.02-1e-7)&(self.peak_z-self.start_z>=.03)&self.up&~self.bad
        self.count+=valid.long();self.air&=~landed;self.had_support|=supported;self.previous_z.copy_(root_z)
        return valid
