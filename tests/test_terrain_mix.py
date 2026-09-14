import unittest

from parkour.terrain_mix import build_mix, expand_fractions, mix_groups
from parkour.curriculum_maps import build_mixed_discrete_axes


class TerrainMixTest(unittest.TestCase):
    def test_fractions_range(self):
        self.assertEqual(expand_fractions({"min": .6, "max": 1., "count": 5}), [.6, .7, .8, .9, 1.])
        self.assertEqual(expand_fractions([.5, {"base": .5, "gap": .7}]), [.5, {"base": .5, "gap": .7}])

    def test_groups_partition_envs(self):
        spec = {"seeds": [1, 2], "fractions": {"min": .5, "max": 1., "count": 3}}
        groups = mix_groups(spec, 2048)
        self.assertEqual(len(groups), 6)
        self.assertEqual(groups[0]["env_start"], 0)
        self.assertEqual(groups[-1]["env_stop"], 2048)
        for a, b in zip(groups, groups[1:]):
            self.assertEqual(a["env_stop"], b["env_start"])
        self.assertEqual(groups[0]["layout"], build_mixed_discrete_axes(1, .5))
        self.assertEqual(len({len(g["layout"]["surfaces"]) for g in groups}), 1)

    def test_weights(self):
        groups = mix_groups({"seeds": [1], "fractions": [.5, 1.], "weights": [3, 1]}, 400)
        self.assertEqual([g["env_stop"] - g["env_start"] for g in groups], [300, 100])

    def test_rejects_too_few_envs(self):
        with self.assertRaises(ValueError):
            mix_groups({"seeds": [1], "fractions": {"min": .5, "max": 1., "count": 8}}, 4)


if __name__ == "__main__":
    unittest.main()
