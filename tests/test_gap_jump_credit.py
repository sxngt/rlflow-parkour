import unittest,torch
from parkour.gap_jump_credit import GapJumpCredit

class GapJumpCreditTest(unittest.TestCase):
    def test_forward_flight_then_both_contacts_once(self):
        credit=GapJumpCredit(3,5,[{'arrival_surface_index':4,'direction_xy':[1.,0.],'projected_top_gap_m':.5}],'cpu')
        credit.reset(torch.arange(3),torch.zeros(3,2))
        targets=torch.tensor([[4,3]]*3)
        credit.observe(torch.ones(3,dtype=torch.bool),torch.zeros(3,dtype=torch.bool),torch.zeros(3,2),targets)
        # Robot0 crosses forward, robot1 hops in place, robot2 has invalid flight.
        credit.observe(torch.zeros(3,dtype=torch.bool),torch.tensor([True,True,False]),torch.tensor([[.3,0.],[0.,0.],[.3,0.]]),targets)
        self.assertEqual(credit.settle(torch.tensor([[4,3]]*3),torch.zeros(3,dtype=torch.bool)).tolist(),[0,0,0])
        accepted=torch.tensor([[4,4]]*3)
        self.assertEqual(credit.settle(accepted,torch.tensor([True,False,False])).tolist(),[0,0,0])
        self.assertEqual(credit.settle(accepted,torch.zeros(3,dtype=torch.bool)).tolist(),[1,0,0])
        self.assertEqual(credit.settle(accepted,torch.zeros(3,dtype=torch.bool)).tolist(),[0,0,0])
        credit.reset(torch.arange(3),torch.zeros(3,2))
        self.assertFalse(credit.eligible.any());self.assertFalse(credit.paid.any())
