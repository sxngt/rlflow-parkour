import unittest,torch
from parkour.reset_jitter import perturb,validate_jitter
class JitterTests(unittest.TestCase):
 def test_seeded_pose_only_bounds_and_clean_mixture(self):
  root=torch.zeros(128,13);root[:,2]=.35;root[:,3]=1;root[:,7:]=.1
  s={'version':'start_pose_jitter_v1','probability':.5,'xy_m':.025,'yaw_rad':.04}
  a=perturb(root,s,torch.Generator().manual_seed(4));b=perturb(root,s,torch.Generator().manual_seed(4))
  self.assertTrue(torch.equal(a,b));self.assertTrue(torch.equal(a[:,2],root[:,2]));self.assertTrue(torch.equal(a[:,7:],root[:,7:]))
  self.assertLessEqual(float(a[:,:2].abs().max()),.025);self.assertLessEqual(float((2*torch.atan2(a[:,6],a[:,3])).abs().max()),.04)
  self.assertTrue(torch.allclose(a[:,3:7].norm(dim=1),torch.ones(128)));self.assertTrue(((a==root).all(1)).any());self.assertTrue((a!=root).any())
 def test_legacy_identity_and_invalid_contract(self):
  root=torch.ones(2,13);self.assertIs(perturb(root,None,None),root)
  with self.assertRaises(ValueError):validate_jitter({'reset_jitter':{'version':'start_pose_jitter_v1','probability':1,'xy_m':.2,'yaw_rad':.04}})
