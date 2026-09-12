import unittest,torch
from parkour.terminal_policy import handoff_eligible
class TerminalPolicyGateTest(unittest.TestCase):
    def test_no_handoff_during_travel_fast_arrival_tilt_or_finished_episode(self):
        accepted=torch.tensor([[10,10],[10,9],[10,10],[10,10],[10,10],[10,10]])
        root=torch.zeros(6,3);root[2,0]=.31
        velocity=torch.zeros(6,3);velocity[3,0]=1.1
        gravity=torch.zeros(6,3);gravity[:,2]=-1;gravity[4,2]=-.5
        done=torch.tensor([False,False,False,False,False,True])
        self.assertEqual(handoff_eligible(accepted,10,root,torch.zeros(3),velocity,gravity,torch.full((6,),4),done).tolist(),[True,False,False,False,False,False])
        self.assertFalse(handoff_eligible(accepted,10,root,torch.zeros(3),velocity,gravity,torch.zeros(6),done).any())
