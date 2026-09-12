import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import torch
from parkour.chained_progress import ChainedProgress


class ChainTests(unittest.TestCase):
    def test_asynchronous_hops_do_not_finish_or_reset_first_success(self):
        chain = ChainedProgress(3, 'cpu')
        chain.reset(torch.arange(3), torch.tensor([-.02, 0.]))
        steps = torch.tensor([64, 64, 64])
        roots = torch.tensor([[.13, .01], [.11, -.01], [.08, 0.]])
        roots_before = roots.clone()
        decision = chain.resolve(torch.tensor([True, False, False]), torch.zeros(3, dtype=torch.bool), steps)
        self.assertEqual(decision.advance.tolist(), [True, False, False])
        self.assertFalse(decision.success.any())
        self.assertFalse(chain.finished.any())
        with self.assertRaises(RuntimeError):
            chain.resolve(torch.ones(3, dtype=torch.bool), torch.zeros(3, dtype=torch.bool), steps)
        self.assertEqual(chain.commit(steps, roots).tolist(), [0])
        self.assertTrue(torch.equal(roots, roots_before))
        self.assertEqual(chain.local_steps(steps).tolist(), [0, 64, 64])
        self.assertTrue(torch.equal(chain.launch_origin[0], roots[0]))
        self.assertAlmostEqual(chain.launch_origin[1, 0].item(), -.02)
        decision = chain.resolve(torch.tensor([True, True, False]), torch.tensor([False, False, True]), steps + 70)
        self.assertEqual(decision.success.tolist(), [True, False, False])
        self.assertEqual(decision.advance.tolist(), [False, True, False])
        self.assertEqual(decision.failure.tolist(), [False, False, True])
        chain.commit(steps + 70, roots)
        self.assertEqual(chain.completed.tolist(), [2, 1, 0])
        self.assertEqual(chain.local_steps(steps + 70).tolist(), [70, 0, 134])

    def test_deadlines_failure_precedence_and_no_double_count(self):
        chain = ChainedProgress(4, 'cpu')
        decision = chain.resolve(torch.tensor([True, True, False, True]),
                                 torch.tensor([False, True, False, False]),
                                 torch.tensor([200, 200, 200, 400]))
        self.assertEqual(decision.advance.tolist(), [True, False, False, False])
        self.assertEqual(decision.failure.tolist(), [False, True, False, False])
        self.assertEqual(decision.timeout.tolist(), [False, False, True, True])
        chain.commit(torch.tensor([200, 200, 200, 400]), torch.zeros(4, 2))
        decision = chain.resolve(torch.ones(4, dtype=torch.bool), torch.zeros(4, dtype=torch.bool), torch.full((4,), 400))
        self.assertEqual(decision.success.tolist(), [True, False, False, False])
        self.assertEqual(chain.completed.tolist(), [2, 0, 0, 0])
        chain.reset(torch.tensor([2]), torch.tensor([.1, 0.]))
        self.assertEqual(chain.finished.tolist(), [True, True, False, True])
        self.assertEqual(chain.completed.tolist(), [2, 0, 0, 0])

    def test_single_hop_terminal_contract(self):
        chain = ChainedProgress(3, 'cpu', hops=1)
        decision = chain.resolve(torch.tensor([True, False, False]), torch.tensor([False, True, False]), torch.full((3,), 200))
        self.assertFalse(decision.advance.any())
        self.assertEqual(decision.success.tolist(), [True, False, False])
        self.assertEqual(decision.failure.tolist(), [False, True, False])
        self.assertEqual(decision.timeout.tolist(), [False, False, True])
