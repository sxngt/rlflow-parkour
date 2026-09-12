import unittest
import torch
from parkour.pair_target_progress import PairTargetProgress
class PairProgressTest(unittest.TestCase):
    def test_progress_without_all_four_stabilization(self):
        p=PairTargetProgress(2,4,'cpu',hold_steps=3)
        valid=torch.tensor([[True,True,False,False],[True,False,False,False]])
        for _ in range(3):r=p.update(valid)
        self.assertEqual(p.target.tolist(),[[2,1],[1,0]])
        self.assertEqual(r['accepted_now'].tolist(),[[True,False],[False,False]])
        valid=torch.tensor([[False,False,True,True],[False,False,False,False]])
        for _ in range(3):p.update(valid)
        self.assertEqual(p.accepted[0].tolist(),[1,1])
        self.assertEqual(p.target[0].tolist(),[2,1])
        valid=torch.tensor([[True,True,False,False],[False,False,False,False]])
        for _ in range(3):p.update(valid)
        self.assertEqual(p.target[0].tolist(),[3,2])
        # Complete pair targets asynchronously, without requiring body stoppage.
        for _ in range(3):p.update(torch.tensor([[True,True,True,True],[False,False,False,False]]))
        self.assertEqual(p.target[0].tolist(),[3,3])
        for _ in range(3):r=p.update(torch.tensor([[False,False,True,True],[False,False,False,False]]))
        self.assertTrue(r['sequence_completed'][0]);self.assertFalse(r['sequence_completed'][1])
        r=p.update(torch.ones(2,4,dtype=torch.bool));self.assertFalse(r['accepted_now'][0].any())
        indices,mask=p.lookahead();self.assertEqual(indices[0].tolist(),[[3,3],[3,3]])
        self.assertEqual(mask[0].tolist(),[[True,False],[True,False]])
        before=p.target[1].clone();p.reset(torch.tensor([0]));self.assertTrue(torch.equal(before,p.target[1]))
    def test_contact_must_be_contiguous_and_validated(self):
        p=PairTargetProgress(1,3,'cpu',hold_steps=3)
        yes=torch.ones(1,4,dtype=torch.bool)
        p.update(yes);p.update(yes);p.update(torch.zeros_like(yes));p.update(yes)
        self.assertEqual(p.target.tolist(),[[1,0]])
        with self.assertRaises(ValueError):p.update(torch.ones(1,4))
    def test_either_quorum_requires_one_contiguous_valid_contact(self):
        p=PairTargetProgress(1,4,'cpu',quorum='either',initial_rear_pending=True)
        contact=torch.tensor([[True,False,False,False]])
        for _ in range(3):r=p.update(contact)
        self.assertEqual(p.accepted.tolist(),[[1,-1]])
        self.assertEqual(p.target.tolist(),[[2,0]])
        self.assertTrue(r['accepted_now'][0,0]);self.assertFalse(r['sequence_completed'][0])
