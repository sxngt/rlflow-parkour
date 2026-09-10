import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.sequence import contact_events,stable_landing

class StabilityTests(unittest.TestCase):
    def test_three_support_gate_rejects_two_support_lift(self):
        t=lambda x:torch.tensor([x])
        args=(t(0),t(True),t(1),t(0),t(False),t(.04),t(0.),t(0.),t(2),t(True),.025,.035,2,4)
        self.assertTrue(contact_events(*args)[3].item())
        self.assertFalse(contact_events(*args,min_support=3)[3].item())
    def test_final_stability_requires_completed_sequence_and_all_limits(self):
        spec={'final_vz_max_m_s':.1,'final_angular_speed_max_rad_s':.5,'final_height_error_max_m':.04}
        stages=torch.tensor([4,3,4,4,4,4,4])
        contacts=torch.ones(7,4,dtype=torch.bool);contacts[2,0]=False
        errors=torch.zeros(7,4);errors[3,1]=.03
        vz=torch.zeros(7);vz[4]=.11
        omega=torch.zeros(7);omega[5]=.6
        height=torch.zeros(7);height[6]=.05
        self.assertEqual(stable_landing(stages,contacts,errors,vz,omega,height,.025,spec).tolist(),[True,False,False,False,False,False,False])
