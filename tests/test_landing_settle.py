import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.jump_events import landing_settle_cost
class LandingSettleTests(unittest.TestCase):
 def test_only_after_landing_and_both_velocity_directions(self):
  vz=torch.tensor([1.,0.,.5,-.5,0.])
  contact=torch.tensor([[0,0,0,0],[1,1,1,1],[1,1,1,1],[1,1,1,1],[1,0,1,0]],dtype=torch.bool)
  landed=torch.tensor([False,True,True,True,True])
  cost=landing_settle_cost(vz,contact,landed,2.,1.)
  self.assertTrue(torch.equal(cost,torch.tensor([0.,0.,.5,.5,.5])))
  self.assertTrue(landing_settle_cost(vz,contact,landed,0.,0.).eq(0).all())
