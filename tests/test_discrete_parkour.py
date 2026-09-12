import unittest,math
from parkour.shared_terrain import build_discrete_parkour
from parkour.receding_surface_planner import plan_surfaces
class DiscreteTests(unittest.TestCase):
    def test_separation_and_reconstruction(self):
        for level in ('easy','medium','hard'):
            m=build_discrete_parkour(level,1)
            self.assertEqual(m,build_discrete_parkour(level,1))
            self.assertEqual(len(m['gap_locations']),16)
            for i,gap in enumerate(m['gap_locations'],1):
                a,b=m['surfaces'][i-1:i+1];d=gap['direction_xy']
                projected=sum((b['top_center_m'][k]-a['top_center_m'][k])*d[k] for k in (0,1))
                half=lambda s:sum(abs(sum(s['rotation_local_to_world'][k][j]*d[k] for k in (0,1)))*s['size_m'][j]/2 for j in range(3))
                self.assertGreater(projected-half(a)-half(b),.15)
    def test_four_step_and_replanning(self):
        m=build_discrete_parkour('easy',1)
        a=plan_surfaces(m,'surface_0',[0,0],[1,0],budget_ms=100)
        self.assertEqual(a['status'],'planned');self.assertEqual(len(a['surface_ids']),4)
        m['surfaces'].reverse()
        b=plan_surfaces(m,'surface_0',[0,0],[1,0],budget_ms=100)
        self.assertEqual(a['surface_ids'],b['surface_ids'])
        c=plan_surfaces(m,'surface_0',[0,0],[1,0],blocked=a['surface_ids'],budget_ms=100)
        self.assertEqual(c['status'],'no_plan')
