import unittest
import torch
from parkour.flight_travel import FlightTravel,TravelLandingReward

class TravelRewardTests(unittest.TestCase):
    def test_once_and_failure_cannot_be_repaired(self):
        t=FlightTravel(3,'cpu');r=TravelLandingReward(3,'cpu')
        cmd=torch.tensor([.05,.05,.05]);failure=torch.tensor([False,True,False])
        self.assertEqual(r.collect(t,cmd,failure,4,.03).sum().item(),0)
        t.launch(torch.ones(3,dtype=torch.bool),torch.tensor([[0.,0.],[0.,0.],[.1,0.]]),torch.zeros(2),.06)
        t.touch(torch.ones(3,dtype=torch.bool),torch.tensor([[.05,0.],[.05,0.],[.15,0.]]))
        self.assertTrue(torch.allclose(r.collect(t,cmd,failure,4,.03),torch.tensor([4.,0.,0.])))
        self.assertEqual(r.collect(t,cmd,torch.zeros(3,dtype=torch.bool),4,.03).sum().item(),0)
        t.reset([0]);r.reset([0]);t.launch(torch.tensor([True,False,False]),torch.zeros(3,2),torch.zeros(2),.06)
        t.touch(torch.tensor([True,False,False]),torch.tensor([[.02,0.],[0.,0.],[0.,0.]]))
        value=r.collect(t,cmd,failure,4,.03)
        self.assertAlmostEqual(value[0].item(),4*torch.exp(torch.tensor(-1.)).item(),places=5)
        self.assertEqual(value[1:].sum().item(),0)

    def test_invalid_scale(self):
        with self.assertRaises(ValueError):
            TravelLandingReward(1,'cpu').collect(FlightTravel(1,'cpu'),torch.zeros(1),torch.zeros(1,dtype=torch.bool),4,0)
