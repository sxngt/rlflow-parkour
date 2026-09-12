"""Last pre-flight foot contact observations for full-platform gap audits."""
import torch
class LaunchSupportHistory:
    def __init__(self,count,device):
        self.positions=torch.zeros(count,4,3,device=device)
        self.force_z=torch.zeros(count,4,device=device)
        self.seen=torch.zeros(count,4,dtype=torch.bool,device=device)
    def reset(self,ids):
        self.positions[ids]=0;self.force_z[ids]=0;self.seen[ids]=False
    def update(self,force,positions,flight_seen):
        active=(~flight_seen[:,None])&(force.norm(dim=-1)>2)
        self.positions[active]=positions[active]
        self.force_z[active]=force[:,:,2][active]
        self.seen|=active
    def departure_valid(self,surface):
        x0,x1,y0,y1=surface['bounds_xy_m'];z=surface['top_z_m'];p=self.positions
        return (self.seen&(self.force_z>2)&(p[:,:,0]>=x0)&(p[:,:,0]<=x1)&
                (p[:,:,1]>=y0)&(p[:,:,1]<=y1)&(p[:,:,2]>=z)&(p[:,:,2]<=z+.04)).all(dim=1)
