import unittest
import torch
from parkour.first_touch import FirstTouch
from parkour.flight_travel import FlightTravel, TravelLandingReward


class CoupledTravelTests(unittest.TestCase):
    def setUp(self):
        self.t=FlightTravel(3,'cpu');self.f=FirstTouch(3,'cpu')
        self.r=TravelLandingReward(3,'cpu','coupled_first_touch_v1')
        self.cmd=torch.full((3,),.15);self.fail=torch.zeros(3,dtype=torch.bool)
        self.t.launch(torch.ones(3,dtype=torch.bool),torch.zeros(3,2),torch.zeros(2),.03)
        self.t.touch(torch.ones(3,dtype=torch.bool),torch.tensor([[.15,0.],[.15,0.],[.15,0.]]))

    def collect(self):
        return self.r.collect(self.t,self.cmd,self.fail,12.,.03,self.f,.05)

    def test_partial_contact_waits_then_pays_once(self):
        self.f.seen[:,:3]=True
        self.assertEqual(self.collect().sum(),0)
        self.f.seen[:,3]=True;self.f.errors[1,3]=.05;self.f.errors[2,0]=.1
        self.assertTrue(torch.allclose(self.collect(),12*torch.exp(torch.tensor([0.,-1.,-2.]))))
        self.f.errors.zero_()
        self.assertEqual(self.collect().sum(),0)

    def test_failure_before_completion_cannot_be_repaired(self):
        self.fail[0]=True;self.assertEqual(self.collect().sum(),0)
        self.fail.zero_();self.f.seen[:]=True
        self.assertEqual(self.collect()[0],0)
        self.r.reset([0]);self.f.reset([0]);self.t.reset([0])
        self.assertEqual(self.collect().sum(),0)

    def test_invalid_launch_and_distance_error(self):
        self.f.seen[:]=True;self.t.launch_ok[0]=False;self.t.touch_xy[1,0]=.12
        value=self.collect()
        self.assertEqual(value[0],0)
        self.assertAlmostEqual(value[1].item(),12*torch.exp(torch.tensor(-1.)).item(),places=5)

    def test_first_touch_latches_cannot_be_corrected(self):
        target=torch.zeros(3,4,2);xy=target.clone();xy[:,3,0]=.05
        force=torch.zeros(3,4,3);force[:,:,2]=10
        self.f.update(torch.ones(3,dtype=torch.bool),force,xy,target)
        self.f.update(torch.ones(3,dtype=torch.bool),force,target,target)
        self.assertTrue(torch.allclose(self.collect(),torch.full((3,),12*torch.exp(torch.tensor(-1.)).item())))

    def test_invalid_mode_or_scale(self):
        with self.assertRaises(ValueError):TravelLandingReward(1,'cpu','typo')
        with self.assertRaises(ValueError):self.r.collect(self.t,self.cmd,self.fail,12.,.03,self.f,0.)
