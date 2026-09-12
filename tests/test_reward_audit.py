import json
import tempfile
from pathlib import Path
import unittest
import torch
from parkour.reward_audit import RewardAudit

class RewardAuditTests(unittest.TestCase):
    def test_terminal_step_included_subsequent_reset_excluded(self):
        a=RewardAudit()
        a.collect(torch.tensor([3.,7.]),{'a':torch.tensor([1.,3.]),'b':torch.tensor([2.,4.])},torch.tensor([False,False]))
        a.collect(torch.tensor([100.,5.]),{'a':torch.tensor([90.,2.]),'b':torch.tensor([10.,3.])},torch.tensor([True,False]))
        with tempfile.TemporaryDirectory() as d:
            a.close(Path(d),[{'id':'a'},{'id':'b'}],.02)
            r=json.loads((Path(d)/'reward-components.json').read_text())
            self.assertEqual([e['actual_return'] for e in r['episodes']],[3.,12.])
            self.assertEqual([e['steps'] for e in r['episodes']],[1,2])
    def test_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            RewardAudit().collect(torch.tensor([3.]),{'a':torch.tensor([1.])},torch.tensor([False]))
