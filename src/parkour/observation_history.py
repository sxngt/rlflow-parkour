"""Clock-aware observation history and shared per-frame normalization."""
import torch
from rsl_rl.modules import EmpiricalNormalization


class ObservationHistory:
    def __init__(self,count,device,spec):
        self.spec=spec
        self.frames=torch.zeros(count,spec['frames'],spec['base_observation_dim'],device=device)
        self.last_clock=torch.full((count,),-1,dtype=torch.long,device=device)
        self.count=torch.zeros(count,dtype=torch.long,device=device)

    def reset(self,ids):
        self.frames[ids]=0;self.last_clock[ids]=-1;self.count[ids]=0

    def encode(self,current,clock):
        if current.shape!=(len(self.frames),self.spec['base_observation_dim']):
            raise ValueError('Wrong current observation shape')
        if self.spec['mode']=='zero_control':
            extra=self.frames.shape[1]*self.frames.shape[2]+self.frames.shape[1]-1-current.shape[1]
            return torch.cat((current,torch.zeros(len(current),extra,device=current.device,dtype=current.dtype)),dim=1)
        discontinuity=(clock<self.last_clock)|(clock>self.last_clock+1)
        self.reset(discontinuity.nonzero(as_tuple=False).flatten())
        advance=clock!=self.last_clock
        ids=advance.nonzero(as_tuple=False).flatten()
        self.frames[ids,1:]=self.frames[ids,:-1].clone()
        self.count[ids]=(self.count[ids]+1).clamp_max(self.frames.shape[1])
        self.last_clock.copy_(clock)
        # Repeated observation reads at the same control step replace only current.
        self.frames[:,0]=current
        valid=(torch.arange(1,self.frames.shape[1],device=current.device)[None,:]<self.count[:,None]).to(current.dtype)
        return torch.cat((current,self.frames[:,1:].flatten(1),valid),dim=1)


class HistoryNormalization(EmpiricalNormalization):
    """Update moments once from current frame; share them across valid history."""
    def __init__(self,spec):
        super().__init__(shape=[spec['base_observation_dim']])
        self.spec=spec

    def forward(self,x):
        dimension=self.spec['base_observation_dim'];frames=self.spec['frames']
        current=super().forward(x[:,:dimension])
        history=x[:,dimension:dimension*frames].reshape(-1,frames-1,dimension)
        valid=x[:,dimension*frames:]
        normalized=(history-self._mean[:,None,:])/(self._std[:,None,:]+self.eps)
        normalized=normalized*valid[:,:,None]
        return torch.cat((current,normalized.flatten(1),valid),dim=1)
