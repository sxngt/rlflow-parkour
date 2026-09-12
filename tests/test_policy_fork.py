import copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
import torch
from parkour.learning import make_algorithm
from parkour.policy_fork import initialize_fork,validate_fork_configs
ROOT=Path(__file__).resolve().parents[1]

class PolicyForkTest(unittest.TestCase):
    def setUp(self):
        self.parent=json.loads((ROOT/'configs/p2-27-continuous.json').read_text())
        self.target=json.loads((ROOT/'configs/p2-29-split.json').read_text())
        env=SimpleNamespace(cfg=SimpleNamespace(observation_space=3),device='cpu',num_envs=2)
        self.source,self.source_norm=make_algorithm(self.parent,env)
        self.dest,self.norm=make_algorithm(self.target,env)
        self.source.policy.std_cap.fill_(.05)
        self.data={'config':self.parent,'model':copy.deepcopy(self.source.policy.state_dict()),'normalizer':copy.deepcopy(self.source_norm.state_dict()),'completed_iterations':1600,'total_environment_steps':39321600}

    def test_copy_weights_keep_new_optimizer_rng_and_controls(self):
        before=torch.get_rng_state().clone()
        result=initialize_fork(self.data,self.target,self.dest,self.norm)
        self.assertTrue(torch.equal(before,torch.get_rng_state()))
        self.assertFalse(self.dest.optimizer.state)
        for k,v in self.dest.policy.state_dict().items():
            if k!='std_cap':self.assertTrue(torch.equal(v,self.data['model'][k]),k)
        for k,v in self.norm.state_dict().items():self.assertTrue(torch.equal(v,self.data['normalizer'][k]),k)
        self.assertAlmostEqual(float(self.dest.policy.std_cap),.1,places=6)
        self.assertEqual(result['initial_environment_steps'],0)

    def test_reject_reward_seed_and_calibration_changes(self):
        for mutation in ('reward','seed','calibration'):
            bad=copy.deepcopy(self.target)
            if mutation=='reward':bad['jump']['travel_reward_weight']=100
            elif mutation=='seed':bad['seed']+=1
            else:bad['terrain_contract']['reference_sha256']='a'*64
            with self.assertRaises(ValueError):validate_fork_configs(self.parent,bad)

    def test_invalid_normalizer_does_not_partially_copy_policy(self):
        before=copy.deepcopy(self.dest.policy.state_dict())
        key=next(k for k,v in self.data['normalizer'].items() if v.is_floating_point())
        self.data['normalizer'][key].fill_(float('nan'))
        with self.assertRaises(ValueError):initialize_fork(self.data,self.target,self.dest,self.norm)
        for k,v in self.dest.policy.state_dict().items():self.assertTrue(torch.equal(v,before[k]))
