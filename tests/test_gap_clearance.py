import unittest,torch
from parkour.gap_clearance import height_reference,validate_clearance
class ClearanceTests(unittest.TestCase):
    def test_reference_and_domain(self):
        centers=torch.tensor([[0.,0.,0.],[1.,0.,.1]])
        xy=torch.tensor([[0.,0.],[.5,0.],[1.,0.],[1.1,0.]])
        z,active=height_reference(xy,centers,torch.ones(4,dtype=torch.long),.27,.12)
        self.assertTrue(torch.allclose(z,torch.tensor([.27,.44,.37,.37])))
        self.assertEqual(active.tolist(),[True,True,True,False])
        rotated,mask=height_reference(xy.flip(1),centers[:,[1,0,2]],torch.ones(4,dtype=torch.long),.27,.12)
        self.assertTrue(torch.allclose(z,rotated))
    def test_contract(self):
        self.assertIsNone(validate_clearance({}))
        with self.assertRaises(ValueError):validate_clearance({'gap_clearance':{'version':'gap_clearance_v1','apex_m':float('nan'),'height_cost':80.}})
