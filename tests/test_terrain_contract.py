import copy
import json
from pathlib import Path
import unittest
from parkour.terrain_contract import training_support, assert_same_terrain


class TerrainContractTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((Path(__file__).resolve().parents[1]/'configs/p2-15-deck.json').read_text())

    def test_layout_and_reference_are_resume_contract(self):
        assert_same_terrain(self.config, copy.deepcopy(self.config))
        for key, value in [('mode', 'flat'), ('reference_sha256', 'a'*64)]:
            other = copy.deepcopy(self.config)
            other['terrain_contract'][key] = value
            with self.assertRaises(ValueError):
                assert_same_terrain(self.config, other)
        with self.assertRaises(ValueError):
            assert_same_terrain({}, self.config)
        assert_same_terrain({}, {})

    def test_generated_layout_and_calibration_validation(self):
        support = training_support(self.config)
        self.assertEqual(support['mode'], 'deck')
        support['mode'] = 'flat'
        self.assertEqual(self.config['terrain_contract']['mode'], 'deck')
        for change in ('shape', 'height'):
            other = copy.deepcopy(self.config)
            if change == 'shape':
                other['terrain_contract']['layout']['surfaces'][0]['size_m'][0] = 10
            else:
                other['terrain_contract']['calibration']['root_state'][2] = float('nan')
            with self.assertRaises(ValueError):
                training_support(other)

    def test_continuous_targets_and_resume_boundary(self):
        cfg = json.loads((Path(__file__).resolve().parents[1]/'configs/p2-27-continuous.json').read_text())
        support = training_support(cfg)
        self.assertEqual(support['mode'], 'continuous')
        with self.assertRaises(ValueError):
            assert_same_terrain(self.config, cfg)
        for location in ('train', 'evaluation', 'curriculum', 'margin'):
            other = copy.deepcopy(cfg)
            if location == 'train':
                other['jump']['train_forward_range_m'][1] = .20
            elif location == 'evaluation':
                other['jump']['evaluation_forward_m'].append(.20)
            elif location == 'curriculum':
                other['jump']['distance_curriculum'][1]['forward_range_m'][0] = -.04
            else:
                other['terrain_contract']['foot_projection_radius_m'] = 0
            with self.assertRaises(ValueError, msg=location):
                training_support(other)
