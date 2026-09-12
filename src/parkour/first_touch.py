"""Latch foot-center XY at the first post-flight physics contact sample."""
import torch

class FirstTouch:
    def __init__(self,count,device):
        self.seen=torch.zeros(count,4,dtype=torch.bool,device=device)
        self.positions=torch.zeros(count,4,2,device=device)
        self.errors=torch.zeros(count,4,device=device)
    def reset(self,ids):
        self.seen[ids]=False;self.errors[ids]=0;self.positions[ids]=0
    def update(self,flight_seen,force,foot_xy,target_xy):
        new=flight_seen[:,None]&(force.norm(dim=-1)>5)&~self.seen
        error=(foot_xy-target_xy).norm(dim=-1)
        self.positions=torch.where(new[:,:,None],foot_xy,self.positions)
        self.errors=torch.where(new,error,self.errors)
        self.seen|=new
        return new
    def within(self,radius):
        return self.seen.all(dim=1)&(self.errors<=radius).all(dim=1)
