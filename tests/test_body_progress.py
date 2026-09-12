import unittest,torch
from parkour.body_progress import progress_reward
class BodyProgressTest(unittest.TestCase):
    def test_stationary_and_round_trip_have_no_reward(self):
        start=torch.tensor([[0.,0.,0.]]);end=torch.tensor([[.1,0.,0.]]);goal=torch.tensor([[1.,0.,0.]])
        self.assertEqual(progress_reward(start,start,goal,10.).item(),0.)
        self.assertAlmostEqual(progress_reward(start,end,goal,10.).item(),1.,places=5)
        self.assertAlmostEqual((progress_reward(start,end,goal,10.)+progress_reward(end,start,goal,10.)).item(),0.)
        # A bookkeeping target switch with no physical movement cannot pay out.
        self.assertEqual(progress_reward(start,start,goal*3,10.).item(),0.)
