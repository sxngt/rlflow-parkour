import unittest

from parkour.curriculum_maps import build_mixed_discrete_axes, normalize_fractions
from parkour.shared_terrain import build_mixed_discrete


class CurriculumMapsTest(unittest.TestCase):
    def test_uniform_matches_original(self):
        for f in (.25, .5, .75, 1.):
            a, b = build_mixed_discrete_axes(1, f), build_mixed_discrete(1, f)
            self.assertEqual(a['surfaces'], b['surfaces'], f)
            self.assertEqual(a['gap_locations'], b['gap_locations'], f)
            self.assertEqual(a['scenario_contract'], 'mixed_discrete_v1')

    def test_axes_only_change_their_geometry(self):
        base = build_mixed_discrete_axes(1, .25)
        gap = build_mixed_discrete_axes(1, {"base": .25, "gap": .5})
        self.assertEqual([s['size_m'] for s in base['surfaces']], [s['size_m'] for s in gap['surfaces']])
        self.assertNotEqual(base['gap_locations'][5]['full_box_clearance_m'], gap['gap_locations'][5]['full_box_clearance_m'])
        self.assertEqual(gap['scenario_contract'], 'mixed_discrete_axes_v1')
        self.assertIsNone(gap['difficulty_fraction'])

    def test_fraction_validation(self):
        with self.assertRaises(ValueError):
            normalize_fractions({"bogus": .5})
        with self.assertRaises(ValueError):
            normalize_fractions({"gap": 1.5})
        self.assertEqual(normalize_fractions(.4)["turn"], .4)


if __name__ == "__main__":
    unittest.main()
