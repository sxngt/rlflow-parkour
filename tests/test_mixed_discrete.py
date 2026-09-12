import copy,json,unittest
from pathlib import Path
from parkour.shared_terrain import build_mixed_discrete,build_discrete_parkour,world_point
from parkour.terrain_contract import training_support

class MixedGeometryTests(unittest.TestCase):
 def test_separated_full_cuboids_and_preserved_approach(self):
  for fraction in (.25,.5,.75,1.):
   c=build_mixed_discrete(1,fraction)
   self.assertEqual(c['surfaces'][:4],build_discrete_parkour('medium',1,24,.75)['surfaces'][:4])
   self.assertEqual(len(c['gap_locations']),24)
   for gap in c['gap_locations']:
    i=gap['arrival_surface_index'];d=gap['direction_xy'];bounds=[]
    for s in c['surfaces'][i-1:i+1]:
     projections=[sum(d[k]*world_point(s,[x*s['size_m'][0]/2,y*s['size_m'][1]/2,z*s['size_m'][2]])[k] for k in (0,1)) for x in (-1,1) for y in (-1,1) for z in (-1,0)]
     bounds.append((min(projections),max(projections)))
    self.assertGreater(bounds[1][0]-bounds[0][1],.1)
  full=build_mixed_discrete(1,1.)
  self.assertLessEqual(min(s['size_m'][1] for s in full['surfaces']),.50)
  self.assertGreaterEqual(max(s['top_center_m'][2] for s in full['surfaces']),.48)
 def test_contract_rejects_unrecorded_geometry_edits(self):
  config=json.loads(Path('configs/p3-70-control.json').read_text())
  self.assertEqual(training_support(config),config['terrain_contract'])
  changed=copy.deepcopy(config);changed['terrain_contract']['layout']['surfaces'][6]['size_m'][0]+=.01
  with self.assertRaises(ValueError):training_support(changed)
