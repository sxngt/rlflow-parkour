import math
import unittest
from parkour.shared_terrain import surface,local_point,world_point,contains_contact_center,build_shared_course
class SharedTerrainTest(unittest.TestCase):
    def test_oriented_contact_coordinates(self):
        s=surface('s',[1.,2.,.3],[.7,.6,.2],[15,-20,40])
        for point in ([.1,-.12,.02],[0,0,0],[.35,0,.02]):
            self.assertTrue(all(abs(a-b)<1e-12 for a,b in zip(point,local_point(s,world_point(s,point)))))
        self.assertTrue(contains_contact_center(s,world_point(s,[.1,.1,.02])))
        self.assertFalse(contains_contact_center(s,world_point(s,[.35,0,.02])))
        self.assertFalse(contains_contact_center(s,world_point(s,[0,0,-.1])))
        self.assertAlmostEqual(sum(x*x for x in s['normal']),1)
        self.assertAlmostEqual(sum(x*x for x in s['orientation_wxyz']),1)
    def test_diverse_geometry_without_foot_ownership(self):
        for kind in ('blocks','ramps','turns','mixed'):
            c=build_shared_course(kind);self.assertEqual(len(c['surfaces']),7)
            self.assertTrue(all('foot' not in s and s['contact_ownership']=='shared' for s in c['surfaces']))
            self.assertNotIn('landing_targets',c)
        self.assertTrue(any(abs(s['normal'][0])>.01 for s in build_shared_course()['surfaces']))
