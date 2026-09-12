import unittest,itertools,torch
from parkour.bounding_style import bounding_mask
class BoundingStyleTest(unittest.TestCase):
    def test_complete_contact_truth_table(self):
        rows=list(itertools.product([False,True],repeat=4))
        actual=bounding_mask(torch.tensor(rows))
        self.assertEqual([row for row,yes in zip(rows,actual) if yes],[(False,False,False,False),(False,False,True,True),(True,True,False,False)])
