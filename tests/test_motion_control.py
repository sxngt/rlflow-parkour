import unittest
import torch
from parkour.motion_control import limit_reference,validate_motion
class MotionTests(unittest.TestCase):
    def test_rate_and_convergence(self):
        previous=torch.zeros(2,12);desired=torch.ones_like(previous)
        for _ in range(10):
            result=limit_reference(desired,previous,.5,.02,8.)
            self.assertLessEqual(float(((result-previous)*.5).abs().max()),.160001)
            previous=result
        self.assertTrue(torch.allclose(previous,desired))
    def test_invalid(self):
        self.assertIsNone(validate_motion({}))
        with self.assertRaises(ValueError):validate_motion({'motion_control':{}})
    def test_positive_progress_cap_keeps_backward_penalty(self):
        from parkour.motion_control import capped_progress
        r=torch.tensor([-.5,0.,.1,.9])
        actual=capped_progress(r,10.,1.8,.02)
        self.assertTrue(torch.allclose(actual,torch.tensor([-.5,0.,.1,.36])))
