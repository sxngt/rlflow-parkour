import unittest,torch
from parkour.exploration import BoundedActorCritic
class BoundedMeanTest(unittest.TestCase):
    def policy(self,bounded):
        p=BoundedActorCritic(3,3,12,min_std=.12,max_std=.25,bounded_mean=bounded,actor_hidden_dims=[4],critic_hidden_dims=[4],init_noise_std=.25)
        with torch.no_grad():
            for v in p.actor.parameters():v.zero_()
            p.actor[-1].bias.fill_(3.8)
        return p
    def test_rollout_and_inference_mean_match_and_explore_below_limit(self):
        p=self.policy(True);obs=torch.zeros(4096,3);p.update_distribution(obs)
        self.assertTrue(torch.equal(p.act_inference(obs),p.action_mean))
        self.assertLessEqual(float(p.action_mean.abs().max()),1.)
        torch.manual_seed(42);actions=p.distribution.sample()
        self.assertGreater(float((actions<1).float().mean()),.45)
        before=p.get_actions_log_prob(actions).detach();p.update_distribution(obs)
        self.assertTrue(torch.equal(before,p.get_actions_log_prob(actions).detach()))
        loss=-p.get_actions_log_prob(torch.full_like(actions,.75)).mean();loss.backward()
        self.assertGreater(float(p.actor[-1].bias.grad.abs().sum()),0.)
    def test_legacy_mean_is_unchanged(self):
        p=self.policy(False);obs=torch.zeros(2,3);p.update_distribution(obs)
        self.assertTrue(torch.equal(p.action_mean,torch.full((2,12),3.8)))
