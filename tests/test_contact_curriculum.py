import copy,unittest
from parkour.contact_curriculum import radius_for_update
from parkour.launch_curriculum import checkpoint_state
class ContactCurriculumTest(unittest.TestCase):
    def test_strict_eval_and_resume_boundary(self):
        c={'task':'a1_continuous_tracker_v1','success_radius_m':.06,'contact_curriculum':{'kind':'contact_precision_v1',
             'stages':[{'start_update':0,'radius_m':.25},{'start_update':20,'radius_m':.06}]}}
        self.assertEqual(radius_for_update(c,19),.25);self.assertEqual(radius_for_update(c,20),.06)
        self.assertEqual(c['success_radius_m'],.06)
        self.assertEqual(checkpoint_state(c,20)['next_contact_radius_m'],.06)
        bad=copy.deepcopy(c);bad['contact_curriculum']['stages'][-1]['radius_m']=.08
        with self.assertRaises(ValueError):radius_for_update(bad,0)
        with self.assertRaises(ValueError):radius_for_update(c,-1)
