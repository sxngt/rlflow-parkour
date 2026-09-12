import copy
import json
from pathlib import Path
import unittest
import torch
from parkour.jump_sampling import sample_distances, target_ranges
from parkour.terrain_contract import training_support

class JumpSamplingTest(unittest.TestCase):
    def test_discrete_reproducible_without_gap_targets(self):
        jump={'train_forward_choices_m':[0.,.15]}
        g=torch.Generator().manual_seed(123)
        state=g.get_state();a=sample_distances(jump,10000,'cpu',g)
        g.set_state(state);b=sample_distances(jump,10000,'cpu',g)
        self.assertTrue(torch.equal(a,b))
        self.assertTrue(((a==0)|(a==torch.tensor(.15))).all())
        self.assertLess(abs(int((a==0).sum())-5000),250)
    def test_range_keeps_previous_rng_and_draws(self):
        g=torch.Generator().manual_seed(42);old=.15*torch.rand(50,generator=g)
        g.manual_seed(42);new=sample_distances({'train_forward_range_m':[0.,.15]},50,'cpu',g)
        self.assertTrue(torch.equal(old,new))
    def test_contract_and_unsupported_combinations(self):
        root=Path(__file__).resolve().parents[1]
        cfg=json.loads((root/'configs/p2-30-mixed.json').read_text())
        self.assertEqual(training_support(cfg)['mode'],'split')
        for values in [[.05],[0,.15,.15],[float('nan')],[],[-.1]]:
            bad=copy.deepcopy(cfg);bad['jump']['train_forward_choices_m']=values
            with self.assertRaises(ValueError):training_support(bad)
        for addition in [{'train_forward_range_m':[0,.15]},{'distance_curriculum':[]}]:
            with self.assertRaises(ValueError):target_ranges({**cfg['jump'],**addition})
