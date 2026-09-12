import unittest
import torch
from parkour.shared_terrain import surface,world_point
from parkour.surface_region import exposed_projection

class ExposedSurfaceTest(unittest.TestCase):
    def check_region(self,surfaces,points,indices):
        def t(key):return torch.tensor([s[key] for s in surfaces],dtype=torch.float64)
        return exposed_projection(torch.tensor([points],dtype=torch.float64),torch.tensor([indices]),t('rotation_local_to_world'),t('top_center_m'),t('center_m'),t('size_m'))[0].tolist()

    def test_overlapping_higher_and_coplanar_blocks_cannot_credit_lower(self):
        a=surface('a',[0,0,0],[1,1,.2],[0,0,0]);b=surface('b',[.3,0,.02],[.4,.4,.2],[0,0,0])
        self.assertEqual(self.check_region([a,b],[[.3,0,.04],[-.3,0,.02],[.3,0,.04]],[0,0,1]),[False,True,True])
        b=surface('b',[.3,0,0],[.4,.4,.2],[0,0,0])
        self.assertEqual(self.check_region([a,b],[[.3,0,.02]],[0]),[False])

    def test_rotated_contact_projects_along_selected_normal(self):
        a=surface('a',[0,0,.1],[1,1,.2],[15,20,35]);b=surface('b',[3,0,0],[1,1,.2],[0,0,0])
        point=world_point(a,[.1,.1,.02])
        self.assertEqual(self.check_region([a,b],[point],[0]),[True])
