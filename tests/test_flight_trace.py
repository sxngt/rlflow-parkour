import unittest
import numpy as np
from parkour.flight_trace import reconstruct_flights

class FlightTraceTest(unittest.TestCase):
    def test_recontact_required_and_collisions_or_drops_rejected(self):
        force=np.zeros((12,4,3));force[[0,9,10,11],:,2]=20
        z=np.array([.3,.31,.32,.34,.36,.38,.37,.36,.35,.34,.33,.33])
        vz=np.ones(12);collision=np.zeros(12)
        events=reconstruct_flights(force,z,vz,collision,.005)
        self.assertEqual(len(events),1);self.assertTrue(events[0]['counted_jump'])
        self.assertEqual(events[0]['takeoff_sample'],1)
        self.assertEqual(events[0]['landing_sample'],9)
        collision[5]=6
        self.assertFalse(reconstruct_flights(force,z,vz,collision,.005)[0]['counted_jump'])
        self.assertFalse(reconstruct_flights(force,-z,-vz,np.zeros(12),.005)[0]['counted_jump'])
        self.assertEqual(reconstruct_flights(force[:9],z[:9],vz[:9],collision[:9],.005),[])
