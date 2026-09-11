"""Single-flight root displacement; excludes walking before the launch latch."""
import torch
import math

class TravelLandingReward:
    """One reward at the first recorded body touchdown, never after correction."""
    def __init__(self,count,device):
        self.paid=torch.zeros(count,dtype=torch.bool,device=device)
    def reset(self,ids):self.paid[ids]=False
    def collect(self,travel,command,failure,weight,scale):
        if not math.isfinite(weight) or weight<0 or not math.isfinite(scale) or scale<=0:
            raise ValueError('Travel reward requires nonnegative weight and positive scale')
        new=travel.touched&~self.paid
        self.paid|=travel.touched
        return new*travel.launch_ok*(~failure)*weight*torch.exp(-(travel.distance()-command).abs()/scale)

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
    def distance_met(self,command,tolerance):
        enough=(command<=1e-6)|(self.distance()>=(command-tolerance).clamp_min(0))
        return self.launched&self.touched&enough
    def valid(self,command,tolerance):
        return self.launch_ok&self.distance_met(command,tolerance)
