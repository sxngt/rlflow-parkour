import copy
import json
from pathlib import Path
import unittest

from parkour.support_assignment import support_assignment, assert_same_support_assignment

ROOT = Path(__file__).resolve().parents[1]


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'configs/p2-36-mixed.json').read_text())
        self.config['support_assignment'] = dict(schema_version=1, single_mode='continuous',
            assignment='fixed_env_id_chain_first', replicate_physics=False)

    def test_partition_geometry_and_input_immutability(self):
        original = copy.deepcopy(self.config)
        plan = support_assignment(self.config)
        a, b = plan['groups']
        self.assertEqual((a['env_start'], a['env_stop'], b['env_start'], b['env_stop']), (0, 512, 512, 1024))
        self.assertEqual(len(a['layout']['surfaces']), 1)
        self.assertEqual(len(b['layout']['surfaces']), 4)
        self.assertTrue(all(s['id'] != 'shared_deck' for s in b['layout']['surfaces']))
        self.assertEqual(self.config, original)
        self.config['support_assignment']['single_mode'] = 'deck'
        other = support_assignment(self.config)
        self.assertEqual(other['groups'][0]['layout'], other['groups'][1]['layout'])

    def test_invalid_partition_and_resume_rejected(self):
        for field, value in [('single_mode', 'split'), ('replicate_physics', True), ('schema_version', 2)]:
            bad = copy.deepcopy(self.config); bad['support_assignment'][field] = value
            with self.assertRaises(ValueError): support_assignment(bad)
        bad = copy.deepcopy(self.config); bad['num_envs'] = 3
        with self.assertRaises(ValueError): support_assignment(bad)
        bad = copy.deepcopy(self.config); del bad['retention_training']
        with self.assertRaises(ValueError): support_assignment(bad)
        other = copy.deepcopy(self.config); other['support_assignment']['single_mode'] = 'deck'
        with self.assertRaises(ValueError): assert_same_support_assignment(self.config, other)
        assert_same_support_assignment(self.config, copy.deepcopy(self.config))
