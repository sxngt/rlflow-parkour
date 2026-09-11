import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.jump_events import apex_progress,landing_height_cost

class JumpShapingTests(unittest.TestCase):
 def test_progress_is_bounded_once_and_resettable(self):
  required=torch.tensor([.05]);previous=torch.zeros(1);total=0.
  for height in [.0,.03,.04,.05,.08,.02,.05]:
   previous,delta=apex_progress(torch.tensor([height]),required,.03,previous)
   self.assertGreaterEqual(delta.item(),0);total+=delta.item()
  self.assertAlmostEqual(total,1.);self.assertAlmostEqual(previous.item(),1.)
  _,delta=apex_progress(torch.tensor([.04]),required,.03,torch.zeros(1))
  self.assertAlmostEqual(delta.item(),.5,places=5)
 def test_height_cost_only_after_touch_is_symmetric_and_bounded(self):
  rise=torch.tensor([-.12,-.06,0,.06,.2,.2])
  landed=torch.tensor([True,True,True,True,True,False])
  self.assertTrue(torch.allclose(landing_height_cost(rise,landed,.06),torch.tensor([4.,1.,0.,1.,4.,0.])))
