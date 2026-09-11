"""Single-flight root displacement; excludes walking before the launch latch."""
import torch

class FlightTravel:
    def __init__(self,count,device):
        self.launched=torch.zeros(count,dtype=torch.bool,device=device)
        self.touched=torch.zeros_like(self.launched)
        self.launch_xy=torch.zeros(count,2,device=device)
        self.touch_xy=torch.zeros_like(self.launch_xy)
        self.launch_ok=torch.zeros_like(self.launched)
    def reset(self,ids):
        for value in (self.launched,self.touched,self.launch_xy,self.touch_xy,self.launch_ok):value[ids]=0
    def launch(self,event,xy,origin,radius):
        new=event&~self.launched
        self.launch_xy[new]=xy[new]
        self.launch_ok[new]=(xy[new]-origin).norm(dim=1)<=radius
        self.launched|=new
    def touch(self,event,xy):
        new=event&self.launched&~self.touched
        self.touch_xy[new]=xy[new];self.touched|=new
    def distance(self):return self.touch_xy[:,0]-self.launch_xy[:,0]
    def valid(self,command,tolerance):
        enough=(command<=1e-6)|(self.distance()>=(command-tolerance).clamp_min(0))
        return self.launched&self.touched&self.launch_ok&enough
