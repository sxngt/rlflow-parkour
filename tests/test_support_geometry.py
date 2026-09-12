import unittest

from parkour.support_geometry import build_support_layout, support_ids_at_xy


class SupportGeometryTest(unittest.TestCase):
    names = ['FL', 'FR', 'RL', 'RR']
    feet = [[.114, .16], [.114, -.16], [-.258, .16], [-.258, -.16]]

    def test_shared_deck_covers_stance_and_targets_but_is_finite(self):
        deck = build_support_layout(self.names, self.feet, mode='deck')
        self.assertEqual(len(deck['surfaces']), 1)
        for x, y in self.feet:
            self.assertTrue(support_ids_at_xy(deck, x, y))
            self.assertTrue(support_ids_at_xy(deck, x+.15, y))
        self.assertFalse(support_ids_at_xy(deck, 2., 0.))

    def test_real_holes_and_matched_targets(self):
        bridge = build_support_layout(self.names, self.feet, mode='continuous')
        split = build_support_layout(self.names, self.feet, mode='split')
        self.assertEqual(bridge['landing_targets'], split['landing_targets'])
        self.assertAlmostEqual(split['gap_width_m'], .06)
        for x, y in self.feet:
            self.assertTrue(support_ids_at_xy(split, x, y))
            self.assertTrue(support_ids_at_xy(split, x+.15, y))
            self.assertFalse(support_ids_at_xy(split, x+.075, y))
            self.assertTrue(support_ids_at_xy(bridge, x+.075, y))
        self.assertTrue(all(s['top_z_m'] == 0 for s in split['surfaces']))

    def test_invalid_or_accidentally_bridged_layout(self):
        for kwargs in ({'travel_m': .08}, {'pad_width_m': 1.},
                       {'catch_floor_z_m': 0.}, {'pad_length_m': float('nan')}):
            with self.assertRaises(ValueError):
                build_support_layout(self.names, self.feet, mode='split', **kwargs)
        with self.assertRaises(ValueError):
            build_support_layout(self.names, [[0, 0]] * 4, mode='continuous')


class CommandedSurfaceTest(unittest.TestCase):
    def test_zero_and_forward_select_distinct_pads(self):
        import json
        from pathlib import Path
        from parkour.support_geometry import expected_goal_surface
        c=json.loads((Path(__file__).resolve().parents[1]/'configs/p2-30-mixed.json').read_text())
        support=c['terrain_contract']
        for i,xy in enumerate(support['calibration']['foot_xy_m']):
            self.assertEqual(expected_goal_surface(support,i,xy,0)['role'],'departure')
            self.assertEqual(expected_goal_surface(support,i,xy,.15)['role'],'landing')
            with self.assertRaises(ValueError):expected_goal_surface(support,i,xy,.05)
