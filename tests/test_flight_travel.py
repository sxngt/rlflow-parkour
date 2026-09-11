import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.flight_travel import FlightTravel
class TravelTests(unittest.TestCase):
 def test_walk_first_reverse_and_stationary_nonzero_rejected(self):
  x=FlightTravel(4,'cpu');origin=torch.tensor([-.047,0.])
  launch=origin.repeat(4,1);launch[0,0]+=.1
  x.touch(torch.ones(4,dtype=torch.bool),launch)
  self.assertFalse(x.touched.any())
  x.launch(torch.ones(4,dtype=torch.bool),launch,origin,.03)
  landing=launch.clone();landing[0,0]+=.2;landing[2,0]-=.1;landing[3,0]+=.13
  x.touch(torch.ones(4,dtype=torch.bool),landing)
  self.assertEqual(x.valid(torch.full((4,),.15),.03).tolist(),[False,False,False,True])
  self.assertEqual(x.distance_met(torch.full((4,),.15),.03).tolist(),[True,False,False,True])
  x.touch(torch.ones(4,dtype=torch.bool),landing+1)
  self.assertTrue(torch.equal(x.touch_xy,landing))
  x.reset(torch.tensor([1]));self.assertFalse(x.launched[1]);self.assertTrue(x.launched[3])
 def test_zero_distance_allows_small_backward_motion(self):
  x=FlightTravel(1,'cpu');origin=torch.tensor([-.047,0.]);start=origin[None,:].clone()
  x.launch(torch.tensor([True]),start,origin,.03)
  x.touch(torch.tensor([True]),start-torch.tensor([[.001,0.]]))
  self.assertTrue(x.valid(torch.tensor([0.]),.03).item())
