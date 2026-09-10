import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import numpy as np
from parkour.diagnostics import summarize

class DiagnosticTests(unittest.TestCase):
    def fixture(self):
        t,n=10,1
        return {'valid':np.ones((t,n),bool),'force':np.zeros((t,n,4,3)),
            'root_z':np.ones((t,n))*.3,'root_vz':np.zeros((t,n)),
            'foot_pos':np.zeros((t,n,4,3)),'foot_vel':np.zeros((t,n,4,3)),
            'active':np.zeros((t,n),int),'torque':np.zeros((t,n,12)),
            'action':np.zeros((t,n,12)),'nonfoot_peak':np.zeros((t,n))}
    def test_flight_threshold_and_reset_exclusion(self):
        a=self.fixture();a['force'][:,:,:,2]=20
        a['force'][2:6]=0
        a['valid'][8:]=False;a['root_z'][8:]=100
        r=summarize(a,.005,['case'],['a','b','c','d'])['results'][0]
        self.assertTrue(r['has_flight_20ms']);self.assertAlmostEqual(r['all_feet_air_time_s'],.02)
        self.assertEqual(r['root_z_range_m'],0)
        a['force'][5,:,:,2]=20
        self.assertFalse(summarize(a,.005,['case'],[])['results'][0]['has_flight_20ms'])
    def test_swing_and_active_foot_travel_not_counted_as_support(self):
        a=self.fixture();a['force'][:,:,:,2]=20
        a['foot_pos'][:,0,0,0]=np.arange(10)
        a['foot_pos'][:,0,1,0]=np.arange(10)
        a['force'][:,0,1]=0
        self.assertEqual(summarize(a,.005,['case'],[])['results'][0]['support_travel_total_m'],0)
