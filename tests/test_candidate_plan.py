import unittest
import torch
from parkour.candidate_plan import gather_plan
class CandidateTests(unittest.TestCase):
    def test_legacy_and_candidate_isolation(self):
        plan=torch.arange(2*7*2*3).reshape(2,7,2,3)
        idx=torch.tensor([[[1,2],[0,1]],[[3,4],[2,3]]])
        expected=plan[torch.arange(2)[None,:,None].expand(2,2,2),idx]
        self.assertTrue(torch.equal(gather_plan(plan,idx),expected))
        batched=plan[None].repeat(2,1,1,1,1);batched[1]+=1000
        actual=gather_plan(batched,idx)
        self.assertTrue(torch.equal(actual[0],expected[0]));self.assertTrue(torch.equal(actual[1],expected[1]+1000))
    def test_zero_candidate_and_surface_margin(self):
        from types import SimpleNamespace
        from parkour.candidate_plan import install_candidates
        plan=torch.zeros(2,7,2,3);plan[:,:,:,2]=.02
        plan[:,:,0,1]=-.16;plan[:,:,1,1]=.16
        env=SimpleNamespace(num_envs=18,device='cpu',plan=plan,surface_rotations=torch.eye(3).repeat(7,1,1),surface_centers=torch.zeros(7,3),surface_halves=torch.full((7,2),.3))
        contract=install_candidates(env)
        self.assertEqual(contract['replicates_per_candidate'],2)
        self.assertTrue(torch.equal(env.candidate_plan[4],plan))
        self.assertTrue(torch.equal(env.candidate_plan[:, :, 0],plan[None,:,0].expand(18,-1,-1,-1)))
        self.assertTrue(torch.equal(env.candidate_plan[:,:,5:],plan[None,:,5:].expand(18,-1,-1,-1,-1)))
        env.surface_halves.fill_(.1)
        with self.assertRaises(ValueError):install_candidates(env)

    def test_existing_baseline_is_preserved_without_offset_accumulation(self):
        from types import SimpleNamespace
        from parkour.candidate_plan import install_candidates
        plan=torch.zeros(2,8,2,3);plan[...,2]=.02
        env=SimpleNamespace(num_envs=9,device='cpu',plan=plan,surface_rotations=torch.eye(3).repeat(8,1,1),surface_centers=torch.zeros(8,3),surface_halves=torch.full((8,2),.3))
        env.candidate_plan=plan[None].repeat(9,1,1,1,1);env.candidate_plan[:,:,2:6,:,0]=.03
        old=env.candidate_plan[4].clone();install_candidates(env,2)
        self.assertTrue(torch.equal(env.candidate_plan[4],old))
        self.assertTrue(torch.allclose(env.candidate_plan[0,:,2:6,:,0],torch.full((2,4,2),-.08)))
