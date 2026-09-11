import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from parkour.diagnostics import jump_first_touches

class FirstTouchTests(unittest.TestCase):
 def test_preflight_reset_and_threshold_samples_do_not_count(self):
  a={'valid':np.ones((5,2),bool),'stage':np.array([[0,0],[1,1],[1,1],[2,2],[2,2]]),
     'force':np.zeros((5,2,4,3)),'foot_pos':np.zeros((5,2,4,3)),'time':np.arange(5)*.005}
  a['force'][0,:,:,2]=100 # prior stance must not count
  a['force'][1,:,:,2]=5 # onset requires >5 N
  a['force'][2:,:,:,2]=6
  a['foot_pos'][2,0,:,0]=.04
  a['foot_pos'][3:,0,:,0]=.5 # later drift must not change first touch
  a['valid'][2:,1]=False # auto-reset data must not count
  episodes=[{'id':str(i),'foot_offsets_xy_m':[[0,0]]*4} for i in range(2)]
  r=jump_first_touches(a,np.zeros((4,2)),episodes,.05)
  self.assertEqual(r[0]['errors_m'],[.04]*4);self.assertEqual(r[0]['times_s'],[.01]*4)
  self.assertTrue(r[0]['all_within']);self.assertEqual(r[1]['errors_m'],[None]*4)
  self.assertFalse(r[1]['all_within'])
