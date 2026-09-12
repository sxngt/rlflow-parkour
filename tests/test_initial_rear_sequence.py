import unittest,torch
from parkour.pair_target_progress import PairTargetProgress
from parkour.shared_terrain import build_long_shared_course,scripted_pair_targets,assert_script_contacts_unoccluded
class RearStartupTest(unittest.TestCase):
    def test_rear_steps_into_fronts_previous_stance(self):
        xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        layout=build_long_shared_course('easy',1)
        plan=scripted_pair_targets(layout,xy,initial_rear_target='front_stance')
        self.assertEqual(plan['positions_m'][1][0],plan['positions_m'][0][0])
        self.assertNotEqual(plan['positions_m'][1][0][0][0],xy[2][0])
        assert_script_contacts_unoccluded(layout,plan)
        p=PairTargetProgress(1,11,'cpu',initial_rear_pending=True)
        self.assertEqual(p.accepted.tolist(),[[0,-1]])
        rear=torch.tensor([[False,False,True,True]])
        for _ in range(3):r=p.update(rear)
        self.assertEqual(p.accepted.tolist(),[[0,0]])
        self.assertEqual(p.target.tolist(),[[1,0]])
        self.assertTrue(r['accepted_now'][0,1])
        for _ in range(3):p.update(torch.tensor([[True,True,False,False]]))
        self.assertEqual(p.target.tolist(),[[2,1]])
        p.reset(torch.tensor([0]));self.assertEqual(p.accepted.tolist(),[[0,-1]])
