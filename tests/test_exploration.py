import unittest
import torch
from torch.distributions import Normal
from parkour.exploration import BoundedActorCritic,cap_for_update


class ExplorationTests(unittest.TestCase):
    def test_shared_distribution_and_checkpoint(self):
        p=BoundedActorCritic(3,3,2,actor_hidden_dims=[4],critic_hidden_dims=[4],min_std=.05,max_std=.2)
        with torch.no_grad():p.std.copy_(torch.tensor([.9,.01]))
        obs=torch.zeros(8,3);action=p.act(obs)
        expected=torch.tensor([.2,.05]).expand(8,2)
        self.assertTrue(torch.allclose(p.action_std,expected))
        self.assertTrue(torch.allclose(p.get_actions_log_prob(action),Normal(p.action_mean,expected).log_prob(action).sum(-1)))
        old=p.get_actions_log_prob(action).detach().clone()
        p.update_distribution(obs)
        self.assertTrue(torch.equal(old,p.get_actions_log_prob(action)))
        p.std_cap.fill_(.1);state={k:v.clone() for k,v in p.state_dict().items()}
        p.std_cap.fill_(.3);p.load_state_dict(state);p.update_distribution(obs)
        self.assertAlmostEqual(float(p.action_std.max()),.1,places=6)

    def test_schedule(self):
        c={'exploration':{'kind':'bounded_gaussian_v1','min_std':.05,'stages':[
            {'start_update':0,'max_std':.35},{'start_update':800,'max_std':.2},{'start_update':1200,'max_std':.1}]}}
        for update,value in [(0,.35),(799,.35),(800,.2),(1199,.2),(1200,.1)]:self.assertEqual(cap_for_update(c,update),value)
        c['exploration']['stages'][-1]['max_std']=.01
        with self.assertRaises(ValueError):cap_for_update(c,0)
        self.assertIsNone(cap_for_update({},0))
