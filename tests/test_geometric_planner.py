import json
from pathlib import Path
import unittest
from parkour.geometric_planner import plan_stances
from parkour.support_geometry import build_support_layout

class PlannerTest(unittest.TestCase):
    def setUp(self):
        c=json.loads((Path(__file__).resolve().parents[1]/'configs/p2-40-weighted.json').read_text())['terrain_contract']
        self.feet=c['calibration']['foot_xy_m']
        self.layout=build_support_layout(c['foot_names'], self.feet, mode='course')
    def test_plan_from_geometry_without_role_labels(self):
        for s in self.layout['surfaces']:
            s.pop('foot');s.pop('role')
        self.layout.pop('landing_targets')
        p=plan_stances(self.layout,self.feet,.30)
        self.assertEqual(p['status'],'planned')
        self.assertEqual([c['forward_m'] for c in p['contacts']],[.15,.30])
    def test_missing_surface_and_unreachable_goal_rejected(self):
        self.layout['surfaces'].pop()
        self.assertEqual(plan_stances(self.layout,self.feet,.30)['status'],'no_plan')
    def test_reach_and_margin_limits(self):
        for kwargs in ({'max_step_m':.14},{'margin_m':.031},{'max_hops':1}):
            self.assertEqual(plan_stances(self.layout,self.feet,.30,**kwargs)['status'],'no_plan')
        self.assertEqual(plan_stances(self.layout,self.feet,.45)['status'],'no_plan')

    def test_changed_map_changes_selected_path(self):
        for s in self.layout['surfaces']:
            k=int(s['role'].split('_')[-1])
            delta=-.05*k
            s['center_m'][0]+=delta
            s['bounds_xy_m'][0]+=delta
            s['bounds_xy_m'][1]+=delta
        p=plan_stances(self.layout,self.feet,.20)
        self.assertEqual(p['status'],'planned')
        self.assertEqual([c['forward_m'] for c in p['contacts']],[.1,.2])

    def test_extended_course_and_horizon(self):
        for hops in (6, 8):
            layout = build_support_layout(['FL','FR','RL','RR'], self.feet, mode='course', course_hops=hops)
            self.assertEqual(len(layout['surfaces']), 4*(hops+1))
            plan = plan_stances(layout,self.feet,.15*hops,max_hops=hops)
            self.assertEqual(plan['status'],'planned')
            self.assertEqual(len(plan['contacts']),hops)
            self.assertEqual(plan_stances(layout,self.feet,.15*hops,max_hops=hops-1)['status'],'no_plan')
