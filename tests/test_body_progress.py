import unittest,torch
from parkour.body_progress import progress_reward, gap_landing_waypoint, waypoint
class BodyProgressTest(unittest.TestCase):
    def test_gap_reference_is_pending_only_and_uses_world_frame(self):
        origins=torch.tensor([[0.,0.,0.],[20.,30.,0.],[40.,60.,0.]])
        targets=torch.zeros(3,4,3)+origins[:,None,:]
        offset=torch.tensor([.02,0.,.25])
        centers=torch.tensor([[0.,0.,0.],[1.,.5,.1]])
        result=gap_landing_waypoint(targets,offset,torch.tensor([1,1,0]),torch.tensor([0,1,0]),
            torch.tensor([False,True]),centers,origins,.28)
        self.assertTrue(torch.allclose(result[0],torch.tensor([1.,.5,.38])))
        self.assertTrue(torch.equal(result[1:],waypoint(targets,offset)[1:]))
        self.assertTrue(torch.equal(progress_reward(origins,origins,result,10.),torch.zeros(3)))
    def test_stationary_and_round_trip_have_no_reward(self):
        start=torch.tensor([[0.,0.,0.]]);end=torch.tensor([[.1,0.,0.]]);goal=torch.tensor([[1.,0.,0.]])
        self.assertEqual(progress_reward(start,start,goal,10.).item(),0.)
        self.assertAlmostEqual(progress_reward(start,end,goal,10.).item(),1.,places=5)
        self.assertAlmostEqual((progress_reward(start,end,goal,10.)+progress_reward(end,start,goal,10.)).item(),0.)
        # A bookkeeping target switch with no physical movement cannot pay out.
        self.assertEqual(progress_reward(start,start,goal*3,10.).item(),0.)
