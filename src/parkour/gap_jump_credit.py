"""At most one credit per gap, after a forward flight and both pair contacts."""
import torch

class GapJumpCredit:
    def __init__(self,count,surfaces,gaps,device):
        self.flags=torch.zeros(surfaces,dtype=torch.bool,device=device)
        self.directions=torch.zeros(surfaces,2,device=device)
        self.widths=torch.zeros(surfaces,device=device)
        for gap in gaps:
            index=gap['arrival_surface_index'];self.flags[index]=True
            self.directions[index]=torch.tensor(gap['direction_xy'],device=device)
            self.widths[index]=gap['projected_top_gap_m']
        self.index=torch.full((count,),-1,dtype=torch.long,device=device)
        self.start=torch.zeros(count,2,device=device)
        self.previous=torch.zeros_like(self.start)
        self.eligible=torch.zeros(count,surfaces,dtype=torch.bool,device=device)
        self.paid=torch.zeros_like(self.eligible)
        self.ids=torch.arange(count,device=device)

    def reset(self,ids,root_xy):
        self.index[ids]=-1;self.start[ids]=root_xy;self.previous[ids]=root_xy
        self.eligible[ids]=False;self.paid[ids]=False

    def observe(self,started,valid_landing,root_xy,targets):
        front,rear=targets[:,0],targets[:,1]
        selected=torch.where(self.flags[front],front,torch.where(self.flags[rear],rear,-1))
        self.index=torch.where(started,selected,self.index)
        self.start=torch.where(started[:,None],self.previous,self.start)
        safe=self.index.clamp_min(0)
        forward=((root_xy-self.start)*self.directions[safe]).sum(1)
        credit=valid_landing&(self.index>=0)&(forward>=self.widths[safe]*.5)
        self.eligible[self.ids[credit],safe[credit]]=True
        self.previous.copy_(root_xy)

    def settle(self,accepted,failure):
        reached=torch.arange(self.flags.numel(),device=self.flags.device)[None,:]<=accepted.amin(dim=1)[:,None]
        new=self.eligible&~self.paid&reached&~failure[:,None]
        self.paid|=new
        return new.sum(dim=1)
