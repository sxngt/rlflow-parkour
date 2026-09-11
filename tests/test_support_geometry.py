import unittest

from parkour.support_geometry import build_support_layout, support_ids_at_xy


class SupportGeometryTest(unittest.TestCase):
    names = ['FL', 'FR', 'RL', 'RR']
    feet = [[.114, .16], [.114, -.16], [-.258, .16], [-.258, -.16]]

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
