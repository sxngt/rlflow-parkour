import unittest
import torch
from parkour.flight_events import FlightEvents
class FlightEventsTest(unittest.TestCase):
    def test_upward_flight_landing_not_falling_or_recount(self):
        f=FlightEvents(2,'cpu');force=torch.zeros(2,4,3);force[:,:,2]=20
        f.update(force,torch.tensor([.3,.3]),torch.zeros(2),torch.zeros(2),.005)
        force[:]=0
        for k in range(8):f.update(force,torch.tensor([.3+.01*(k+1),.3-.01*(k+1)]),torch.tensor([1.,-1.]),torch.zeros(2),.005)
        force[:,:,2]=20
        f.update(force,torch.tensor([.3,.2]),torch.zeros(2),torch.zeros(2),.005)
        self.assertEqual(f.count.tolist(),[1,0])
        self.assertEqual(f.airborne_count.tolist(),[1,1])
        f.update(force,torch.tensor([.3,.2]),torch.zeros(2),torch.zeros(2),.005)
        self.assertEqual(f.count.tolist(),[1,0]);f.reset(torch.tensor([0]));self.assertEqual(f.count.tolist(),[0,0])
