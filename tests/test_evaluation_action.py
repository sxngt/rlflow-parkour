import unittest
import torch
from parkour.evaluation_action import sample_action


class Policy:
    def update_distribution(self, obs):
        self.action_mean = obs
        self.action_std = torch.full_like(obs, .3)


class EvaluationActionTests(unittest.TestCase):
    def test_reproducible_and_isolated(self):
        p=Policy();obs=torch.ones(5000,12)
        a=sample_action(p,obs,torch.Generator().manual_seed(3))
        torch.randn(100)
        b=sample_action(p,obs,torch.Generator().manual_seed(3))
        self.assertTrue(torch.equal(a,b))
        self.assertLess(abs(float(a.mean())-1),.01)
        self.assertLess(abs(float(a.std())-.3),.01)
        self.assertFalse(torch.equal(a,sample_action(p,obs,torch.Generator().manual_seed(4))))
