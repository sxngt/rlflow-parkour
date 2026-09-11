import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.first_touch import FirstTouch

class FirstTouchTests(unittest.TestCase):
 def test_preflight_threshold_once_and_failed_touch_not_repaired(self):
  x=FirstTouch(2,'cpu');force=torch.zeros(2,4,3);force[:,:,2]=6
  target=torch.zeros(2,4,2);pos=target.clone();pos[0,0,0]=.1
  self.assertFalse(x.update(torch.zeros(2,dtype=torch.bool),force,pos,target).any())
  force[1,3,2]=5
  new=x.update(torch.ones(2,dtype=torch.bool),force,pos,target)
  self.assertEqual(new.sum(),7);self.assertFalse(x.within(.05).any())
  force[1,3,2]=6
  new=x.update(torch.ones(2,dtype=torch.bool),force,target,target)
  self.assertEqual(new.sum(),1);self.assertEqual(x.within(.05).tolist(),[False,True])
  self.assertAlmostEqual(x.errors[0,0].item(),.1)
  x.reset(torch.tensor([0]));self.assertFalse(x.seen[0].any());self.assertTrue(x.seen[1].all())
  x.update(torch.ones(2,dtype=torch.bool),force,target,target)
  self.assertTrue(x.within(.05).all())
