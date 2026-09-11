import unittest
import torch
from parkour.landing_precision import precision_reward


class LandingPrecisionTests(unittest.TestCase):
    def test_legacy_and_prelanding_unchanged(self):
        errors = torch.tensor([[0., .03, .05, .1], [.02, .04, .06, .08]])
        expected = torch.exp(-(errors/.06).square()).mean(dim=1)-1
        self.assertTrue(torch.equal(precision_reward(errors, torch.ones(2, dtype=torch.bool)), expected))
        self.assertTrue(torch.equal(precision_reward(errors, torch.zeros(2, dtype=torch.bool), 'worst_after_landing_v1'), expected))

    def test_single_bad_foot_not_diluted_and_permutation_invariant(self):
        errors = torch.zeros(4, 4)
        errors[torch.arange(4), torch.arange(4)] = .06
        landed = torch.ones(4, dtype=torch.bool)
        worst = precision_reward(errors, landed, 'worst_after_landing_v1')
        self.assertTrue(torch.allclose(worst, torch.full((4,), torch.exp(torch.tensor(-1.)).item()-1)))
        self.assertTrue(torch.allclose(worst, 4*precision_reward(errors, landed)))
        self.assertTrue(torch.equal(worst, precision_reward(errors[:, [2, 0, 3, 1]], landed, 'worst_after_landing_v1')))

    def test_equal_errors_and_phase_selection(self):
        errors = torch.full((2, 4), .03)
        landed = torch.tensor([False, True])
        self.assertTrue(torch.equal(precision_reward(errors, landed), precision_reward(errors, landed, 'worst_after_landing_v1')))
        errors[:, 0] = .1
        values = precision_reward(errors, landed, 'worst_after_landing_v1')
        self.assertEqual(values[0], precision_reward(errors, landed)[0])
        self.assertLess(values[1], values[0])

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            precision_reward(torch.zeros(1, 4), torch.tensor([True]), 'rr_only')
