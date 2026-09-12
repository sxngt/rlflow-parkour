import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import torch
from parkour.retention_sampling import sample_goal_indices
from parkour.chain_training import validate_chain_training, assert_same_chain_training

ROOT = Path(__file__).resolve().parents[1]

class SamplingTests(unittest.TestCase):
    def test_ticket_boundaries_and_empty_batch(self):
        with patch('parkour.retention_sampling.torch.randint', return_value=torch.arange(6)):
            self.assertEqual(sample_goal_indices(6,4,'cpu',None,[1,1,1,3]).tolist(),[0,1,2,3,3,3])
        self.assertEqual(sample_goal_indices(0,4,'cpu',None,[1,1,1,3]).numel(),0)

    def test_uniform_rng_and_weighted_frequency(self):
        a=torch.Generator().manual_seed(52);b=torch.Generator().manual_seed(52)
        self.assertTrue(torch.equal(sample_goal_indices(32,4,'cpu',a),torch.randint(4,(32,),generator=b)))
        a=torch.Generator().manual_seed(91)
        draws=sample_goal_indices(60000,4,'cpu',a,[1,1,1,3])
        freq=torch.bincount(draws,minlength=4).float()/60000
        self.assertTrue(torch.all((freq-torch.tensor([1/6,1/6,1/6,1/2])).abs()<.01))

    def test_contract_and_resume(self):
        weighted=json.loads((ROOT/'configs/p2-40-weighted.json').read_text())
        uniform=json.loads((ROOT/'configs/p2-39-coverage.json').read_text())
        validate_chain_training(weighted)
        assert_same_chain_training(weighted,copy.deepcopy(weighted))
        with self.assertRaises(ValueError):assert_same_chain_training(uniform,weighted)
        for weights in ([1,1,1,1],[1,1,1,3.0],[True,1,1,3],[1,1,3],[-1,1,1,3]):
            bad=copy.deepcopy(weighted);bad['retention_training']['single_goal_weights']=weights
            with self.assertRaises(ValueError):validate_chain_training(bad)
