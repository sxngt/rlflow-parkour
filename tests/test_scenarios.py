import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parkour.scenarios import development_scenarios


class ScenarioTests(unittest.TestCase):
    def test_prefix_stable_across_batch_size_and_global_rng(self):
        small = development_scenarios(8)
        random.seed(2)
        for _ in range(50):
            random.random()
        large = development_scenarios(64)
        self.assertEqual(small["episodes"], large["episodes"][:8])
        self.assertEqual(len({row["seed"] for row in large["episodes"]}), 64)
        self.assertEqual(large["split"], "development")

    def test_bounds_and_layout(self):
        for row in development_scenarios()["episodes"]:
            self.assertEqual(len(row["foot_offsets_xy_m"]), 4)
            for xy in row["foot_offsets_xy_m"]:
                self.assertEqual(len(xy), 2)
                self.assertTrue(all(abs(value) <= 0.06 for value in xy))

    def test_reject_invalid_count(self):
        for count in (0, -1, 1001):
            with self.assertRaises(ValueError):
                development_scenarios(count)


if __name__ == "__main__":
    unittest.main()
