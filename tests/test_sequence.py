import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.sequence import contact_events

class ContactSequenceTests(unittest.TestCase):
    def event(self, phase=0, seen=True, lift_count=0, hold_count=0, contact=False,
              clearance=.04, error=.01, height_error=0., support=3, settled=True):
        values=[torch.tensor([x]) for x in (phase,seen,lift_count,hold_count,contact,clearance,error,height_error,support,settled)]
        return contact_events(*values,.025,.035,2,4)

    def test_requires_ground_contact_before_lift(self):
        event=self.event(seen=False,lift_count=2)
        self.assertFalse(event[3].item())

    def test_requires_two_consecutive_air_samples(self):
        self.assertFalse(self.event(lift_count=0)[3].item())
        self.assertTrue(self.event(lift_count=1)[3].item())
        interrupted=self.event(lift_count=1,contact=True)
        self.assertEqual(interrupted[1].item(),0)

    def test_cannot_place_before_lift_phase(self):
        self.assertFalse(self.event(phase=0,contact=True,hold_count=4)[4].item())

    def test_rejects_wrong_height_position_or_missing_support(self):
        for override in ({'height_error':.06},{'error':.1},{'support':1},{'settled':False}):
            self.assertFalse(self.event(phase=1,contact=True,hold_count=3,**override)[4].item())

    def test_place_requires_uninterrupted_dwell(self):
        self.assertFalse(self.event(phase=1,contact=True,hold_count=2)[4].item())
        self.assertTrue(self.event(phase=1,contact=True,hold_count=3)[4].item())
        self.assertEqual(self.event(phase=1,contact=False,hold_count=3)[2].item(),0)

if __name__=='__main__':unittest.main()
