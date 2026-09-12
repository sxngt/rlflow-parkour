import unittest,itertools,torch
from parkour.bounding_style import bounding_mask
class BoundingStyleTest(unittest.TestCase):
    def test_complete_contact_truth_table(self):
        rows=list(itertools.product([False,True],repeat=4))
        actual=bounding_mask(torch.tensor(rows))
        self.assertEqual([row for row,yes in zip(rows,actual) if yes],[(False,False,False,False),(False,False,True,True),(True,True,False,False)])

    def test_terminal_stabilization_does_not_reward_unloaded_feet(self):
        contact=torch.tensor([[True,True,False,False],[False,False,True,True],[True,True,False,False]])
        self.assertEqual(bounding_mask(contact,torch.tensor([True,True,False])).tolist(),[False,False,True])
