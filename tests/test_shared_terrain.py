import math
import unittest
from parkour.shared_terrain import surface,local_point,world_point,contains_contact_center,build_shared_course
class SharedTerrainTest(unittest.TestCase):
    def test_gap_elevation_changes_after_first_approach_only(self):
        from parkour.shared_terrain import build_ten_gap_course,scripted_pair_targets,assert_script_contacts_unoccluded
        plain=build_ten_gap_course('medium',1,1.25)
        xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        for rise in (.05,.1):
            raised=build_ten_gap_course('medium',1,1.25,gap_rise_m=rise)
            self.assertEqual(plain['surfaces'][:4],raised['surfaces'][:4])
            self.assertEqual(plain['gap_locations'],raised['gap_locations'])
            for i,(a,b) in enumerate(zip(plain['surfaces'],raised['surfaces'])):
                self.assertAlmostEqual(b['top_center_m'][2]-a['top_center_m'][2],(i//4)*rise)
            assert_script_contacts_unoccluded(raised,scripted_pair_targets(raised,xy))
    def test_longer_approaches_keep_ten_gaps_and_old_map_exact(self):
        import json
        from pathlib import Path
        from parkour.shared_terrain import build_ten_gap_course,scripted_pair_targets,assert_script_contacts_unoccluded
        stored=json.loads(Path('configs/p3-36-mean-bounded.json').read_text())['terrain_contract']
        self.assertEqual(build_ten_gap_course('medium',1),stored['layout'])
        for level in ('easy','medium','hard'):
            c=build_ten_gap_course(level,1,1.25,5)
            self.assertEqual(c['transitions'],60);self.assertEqual(len(c['surfaces']),61)
            self.assertEqual([g['arrival_surface_index'] for g in c['gap_locations']],list(range(6,61,6)))
            self.assertGreater(c['nominal_path_length_m'],build_ten_gap_course(level,1,1.25)['nominal_path_length_m']+8.)
            assert_script_contacts_unoccluded(c,scripted_pair_targets(c,stored['calibration']['foot_xy_m']))
    def test_ten_gap_route_projected_width_and_exposed_targets(self):
        from parkour.shared_terrain import build_ten_gap_course,scripted_pair_targets,assert_script_contacts_unoccluded
        xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        for level in ('easy','medium','hard'):
            for scale in (.5,1.):
                c=build_ten_gap_course(level,1,scale)
                self.assertEqual(c['planned_gap_count'],10)
                self.assertEqual([g['arrival_surface_index'] for g in c['gap_locations']],list(range(4,41,4)))
                assert_script_contacts_unoccluded(c,scripted_pair_targets(c,xy))
                for g in c['gap_locations']:
                    i=g['arrival_surface_index'];a,b=c['surfaces'][i-1:i+1];direction=g['direction_xy']
                    corners=[]
                    for s in (a,b):
                        corners.append([sum(direction[k]*world_point(s,[x*s['size_m'][0]/2,y*s['size_m'][1]/2,0])[k] for k in (0,1)) for x in (-1,1) for y in (-1,1)])
                    self.assertAlmostEqual(min(corners[1])-max(corners[0]),g['projected_top_gap_m'],places=10)
    def test_medium_preparation_is_explicit_and_generated(self):
        from parkour.shared_terrain import build_long_shared_course,scripted_pair_targets,assert_script_contacts_unoccluded
        full=build_long_shared_course('medium',1);easy=build_long_shared_course('easy',1)
        xy=[[.114,.16],[.114,-.16],[-.258,.16],[-.258,-.16]]
        for fraction in (.25,.5,.75):
            c=build_long_shared_course('medium',1,10,fraction)
            self.assertEqual(c['scenario_contract'],'long_shared_blend_v1')
            self.assertGreater(c['nominal_path_length_m'],easy['nominal_path_length_m'])
            self.assertLess(c['nominal_path_length_m'],full['nominal_path_length_m'])
            assert_script_contacts_unoccluded(c,scripted_pair_targets(c,xy))
        with self.assertRaises(ValueError):build_long_shared_course('hard',1,10,.5)
    def test_extended_routes_and_clone_separation_preserve_ten_transfer_maps(self):
        import json
        from pathlib import Path
        from parkour.shared_terrain import build_long_shared_course,shared_scene_spacing,scripted_pair_targets,assert_script_contacts_unoccluded
        stored=json.loads((Path(__file__).resolve().parents[1]/'configs/p3-25-either-foot-progression.json').read_text())
        self.assertEqual(build_long_shared_course('easy',1),stored['terrain_contract']['layout'])
        self.assertEqual(shared_scene_spacing(build_long_shared_course('hard',1)),14.)
        xy=stored['terrain_contract']['calibration']['foot_xy_m']
        for level in ('easy','medium','hard'):
            for count in (20,30,40):
                c=build_long_shared_course(level,1,count)
                self.assertEqual(len(c['surfaces']),count+1)
                self.assertEqual(c['scenario_contract'],'long_shared_course_v2')
                assert_script_contacts_unoccluded(c,scripted_pair_targets(c,xy))
                # Axis-aligned full cuboid spans plus four metres of margin.
                spacing=shared_scene_spacing(c)
                for axis in (0,1):
                    lo=[];hi=[]
                    for s in c['surfaces']:
                        extent=sum(abs(s['rotation_local_to_world'][axis][j])*s['size_m'][j]/2 for j in range(3))
                        lo.append(s['center_m'][axis]-extent);hi.append(s['center_m'][axis]+extent)
                    self.assertGreaterEqual(spacing,max(hi)-min(lo)+4.)
        for bad in (9,41,10.5,True):
            with self.assertRaises(ValueError):build_long_shared_course('easy',1,bad)
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
