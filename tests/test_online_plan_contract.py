import unittest
from parkour.online_plan_contract import admission
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.pending={'id':3,'activation_step':100}
  self.p={'id':3,'activation_step':100,'accepted':True,'predicted_root':[1.,2.,.3],'predicted_target':[5,4],'start_surface':6}
 def test_valid_scheduled_proposal(self):self.assertEqual(admission(self.p,self.pending,100,[1.,2.,.3],[5,4]),(None,0.))
 def test_late_and_mismatched_response(self):
  self.assertEqual(admission(self.p,self.pending,101,[1.,2.,.3],[5,4])[0],'deadline_missed')
  self.p['id']=2;self.assertEqual(admission(self.p,self.pending,100,[1.,2.,.3],[5,4])[0],'response_identity_mismatch')
 def test_state_contact_and_nan(self):
  self.assertEqual(admission(self.p,self.pending,100,[1.09,2.,.3],[5,4])[0],'stale_state_or_contact')
  self.assertEqual(admission(self.p,self.pending,100,[1.,2.,.3],[6,4])[0],'stale_state_or_contact')
  self.assertEqual(admission(self.p,self.pending,100,[float('nan'),2.,.3],[5,4])[0],'invalid_predicted_state')
