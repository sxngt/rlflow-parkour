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
    def test_terminal_target_stance_not_four_feet_on_two_points(self):
        from parkour.shared_terrain import scripted_pair_targets
        c=build_shared_course();xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        plan=scripted_pair_targets(c,xy);front,rear=plan['positions_m']
        self.assertEqual(front[1:-1],rear[1:-1])
        for i in range(2):
            distance=math.sqrt(sum((a-b)**2 for a,b in zip(front[-1][i],rear[-1][i])))
            self.assertAlmostEqual(distance,.36)
        self.assertEqual(front[0][0],[.114,.16,.02])
    def test_long_maps_have_ten_transfers_and_visible_targets(self):
        from parkour.shared_terrain import build_long_shared_course,scripted_pair_targets,assert_script_contacts_unoccluded
        xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        for level in ('easy','medium','hard'):
            c=build_long_shared_course(level,1);self.assertEqual(len(c['surfaces']),11)
            plan=scripted_pair_targets(c,xy);assert_script_contacts_unoccluded(c,plan)
        # A deliberately raised duplicate block must reject an occluded target.
        import copy
        c=build_long_shared_course('easy',1);plan=scripted_pair_targets(c,xy)
        extra=copy.deepcopy(c['surfaces'][2]);extra['id']='occluder'
        extra['center_m'][2]+=.05;c['surfaces'].append(extra)
        with self.assertRaises(ValueError):assert_script_contacts_unoccluded(c,plan)
