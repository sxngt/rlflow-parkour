import copy
import unittest
from parkour.launch_curriculum import radius_for_update, checkpoint_state

class LaunchCurriculumTest(unittest.TestCase):
    def setUp(self):
        self.c={'task':'a1_directed_jump_v5','target_offset_m':.06,'jump':{'launch_radius_m':.03,'launch_curriculum':[{'start_update':0,'radius_m':.06},{'start_update':800,'radius_m':.045},{'start_update':1200,'radius_m':.03}]}}
    def test_boundaries_and_resume(self):
        for step,expected in [(0,.06),(799,.06),(800,.045),(1199,.045),(1200,.03),(1600,.03)]:
            self.assertEqual(radius_for_update(self.c,step),expected)
            self.assertEqual(checkpoint_state(self.c,step)['next_rollout_radius_m'],expected)
        self.assertEqual(self.c['jump']['launch_radius_m'],.03)
    def test_invalid_schedule(self):
        for stages in [[],[{'start_update':1,'radius_m':.03}],[{'start_update':0,'radius_m':.06}], [{'start_update':0,'radius_m':.02},{'start_update':800,'radius_m':.03}], [{'start_update':0,'radius_m':float('nan')}]]:
            c=copy.deepcopy(self.c);c['jump']['launch_curriculum']=stages
            with self.assertRaises(ValueError):radius_for_update(c,0)
    def test_fixed_legacy(self):
        c=copy.deepcopy(self.c);c['jump'].pop('launch_curriculum')
        self.assertEqual(radius_for_update(c,1600),.03)
        self.assertEqual(checkpoint_state(c,1600),{'kind':'fixed','target_offset_m':.06})
