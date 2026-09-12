"""Independent front/rear contact targets without inter-target physical resets.

Input contact validity must already include selected-surface geometry, normal
force and target precision checks. This module is bookkeeping, not a controller.
"""
import torch

class PairTargetProgress:
    def __init__(self,count,target_count,device,hold_steps=3,quorum='both',initial_rear_pending=False):
        if target_count<2 or hold_steps<1 or quorum not in ('both','either'):
            raise ValueError('Invalid pair-target contract')
        self.initial_rear_pending=initial_rear_pending
        self.count=count;self.target_count=target_count;self.hold_steps=hold_steps;self.quorum=quorum
        self.target=torch.zeros(count,2,dtype=torch.long,device=device)
        self.accepted=torch.zeros_like(self.target)
        self.hold=torch.zeros(count,4,dtype=torch.long,device=device)
        self.age=torch.zeros_like(self.target)
        self.reset(torch.arange(count,device=device))
    def reset(self,ids):
        self.target[ids]=torch.tensor([1,0],device=self.target.device)
        # Legacy stance accepts both initial points; the front-stance variant leaves rear zero pending.
        self.accepted[ids]=0;self.hold[ids]=0;self.age[ids]=0
        if self.initial_rear_pending:self.accepted[ids,1]=-1
    def update(self,valid_contact):
        if valid_contact.shape!=(self.count,4) or valid_contact.dtype!=torch.bool:
            raise ValueError('Need per-foot validated contact booleans in FL/FR/RL/RR order')
        self.age+=1
        self.hold=torch.where(valid_contact,self.hold+1,torch.zeros_like(self.hold)).clamp_max(self.hold_steps)
        ready=(self.hold>=self.hold_steps).reshape(self.count,2,2)
        ready=ready.all(dim=2) if self.quorum=='both' else ready.any(dim=2)
        accepted_now=ready&(self.accepted<self.target)
        self.accepted=torch.where(accepted_now,self.target,self.accepted)
        advance=(self.accepted==self.target)&(self.target<self.target_count-1)
        # Rear feet follow the front pair's previous accepted surface.
        advance[:,1]&=self.accepted[:,0]>=self.target[:,1]+1
        self.target+=advance.long()
        self.age[advance]=0
        self.hold.masked_fill_(advance.repeat_interleave(2,dim=1),0)
        return {'accepted_now':accepted_now,'advanced':advance,
                'sequence_completed':(self.accepted==self.target_count-1).all(dim=1)}
    def lookahead(self):
        indices=torch.stack([self.target,(self.target+1).clamp_max(self.target_count-1)],dim=2)
        valid=torch.ones_like(indices,dtype=torch.bool);valid[:,:,1]=self.target<self.target_count-1
        return indices,valid
