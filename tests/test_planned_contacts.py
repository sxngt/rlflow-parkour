import unittest,torch
from types import SimpleNamespace as S
from parkour.planned_contacts import planned_contacts
class PlannedContactTests(unittest.TestCase):
 def test_active_candidate_and_end_mask(self):
  plan=torch.zeros(2,6,2,3)
  for j in range(6):plan[:,j,:,0]=j
  env=S(plan=plan,candidate_plan=plan[None].repeat(2,1,1,1,1),num_envs=2,device='cpu',progress=S(target=torch.tensor([[1,0],[4,3]])),scene=S(env_origins=torch.tensor([[0.,0,0],[10.,0,0]])),surface_normals=torch.tensor([[0.,0,1.]]).repeat(6,1))
  env.candidate_plan[1,...,1]=.123
  p,n,idx,valid=planned_contacts(env,1)
  self.assertEqual(len(p),10);self.assertEqual(idx.tolist(),[[4,5,5,5],[3,4,5,5]])
  self.assertEqual(valid.tolist(),[[True,True,False,False],[True,True,True,False]])
  self.assertTrue(torch.allclose(p[:,1],torch.full((10,),.123)))
  self.assertEqual(p[:,0].tolist(),[14,14,15,15,13,13,14,14,15,15])
  env.candidate_plan[1,...,1]=.456
  self.assertTrue(torch.allclose(planned_contacts(env,1)[0][:,1],torch.full((10,),.456)))
