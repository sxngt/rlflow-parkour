import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.chain_training import validate_chain_training, assert_same_chain_training


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.chain = json.loads((ROOT / 'configs/p2-34-chain.json').read_text())
        self.single = json.loads((ROOT / 'configs/p2-34-single.json').read_text())

    def test_explicit_contract_and_resume(self):
        self.assertEqual(validate_chain_training(self.chain)['hops'], 2)
        self.assertIsNone(validate_chain_training(self.single))
        assert_same_chain_training(self.chain, copy.deepcopy(self.chain))
        with self.assertRaises(ValueError):
            assert_same_chain_training(self.single, self.chain)

    def test_retention_requires_explicit_fork_and_exact_contract(self):
        from parkour.policy_fork import validate_fork_configs
        mixed = copy.deepcopy(self.chain)
        mixed['retention_training'] = {'schema_version': 1, 'single_fraction': .5,
            'single_goal_choices_m': [0., .15], 'assignment': 'fixed_env_id_chain_first'}
        validate_chain_training(mixed)
        validate_fork_configs(self.chain, mixed)
        assert_same_chain_training(mixed, copy.deepcopy(mixed))
        with self.assertRaises(ValueError): assert_same_chain_training(self.chain, mixed)
        bad = copy.deepcopy(mixed); bad['retention_training']['single_fraction'] = .25
        with self.assertRaises(ValueError): validate_chain_training(bad)
        bad = copy.deepcopy(mixed); del bad['chain_training']
        with self.assertRaises(ValueError): validate_chain_training(bad)

    def test_coverage_goals_require_new_fork(self):
        from parkour.policy_fork import validate_fork_configs
        old = json.loads((ROOT / 'configs/p2-38-continuous.json').read_text())
        new = json.loads((ROOT / 'configs/p2-39-coverage.json').read_text())
        validate_chain_training(new)
        validate_fork_configs(old, new)
        with self.assertRaises(ValueError): assert_same_chain_training(old, new)
        for goals in ([0., .1], [0., .05, .05, .15], [.15, .1, .05, 0.]):
            bad = copy.deepcopy(new); bad['retention_training']['single_goal_choices_m'] = goals
            with self.assertRaises(ValueError): validate_chain_training(bad)

    def test_reject_unvalidated_training_variants(self):
        for key, value in [('episode_seconds', 4.), ('task', 'other')]:
            bad = copy.deepcopy(self.chain); bad[key] = value
            with self.assertRaises(ValueError): validate_chain_training(bad)
        for key, value in [('hops', 3), ('settle_command', 'hold-last'), ('hop_seconds', 3.)]:
            bad = copy.deepcopy(self.chain); bad['chain_training'][key] = value
            with self.assertRaises(ValueError): validate_chain_training(bad)
        for key, value in [('train_forward_range_m', [0., .15]), ('settle_seconds', .1), ('train_forward_choices_m', [.15])]:
            bad = copy.deepcopy(self.chain); bad['jump'][key] = value
            with self.assertRaises(ValueError): validate_chain_training(bad)

    def test_fork_allows_only_validated_episode_change(self):
        from parkour.policy_fork import validate_fork_configs
        parent = json.loads((ROOT / 'configs/p2-31-mixed.json').read_text())
        validate_fork_configs(parent, self.single)
        validate_fork_configs(parent, self.chain)
        bad = copy.deepcopy(self.single); bad['episode_seconds'] = 8.
        with self.assertRaises(ValueError): validate_fork_configs(parent, bad)
        bad = copy.deepcopy(self.chain); bad['jump']['launch_radius_m'] = .1
        with self.assertRaises(ValueError): validate_fork_configs(parent, bad)
