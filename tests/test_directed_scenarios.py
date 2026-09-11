import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.scenarios import directed_jump_scenarios
class DirectedScenarioTests(unittest.TestCase):
 def test_balanced_paired_and_prefix_stable(self):
  spec={'evaluation_forward_m':[0.,.05,.1,.15],'apex_range_m':[.04,.06]}
  rows=directed_jump_scenarios(64,spec)['episodes']
  self.assertEqual(rows[:7],directed_jump_scenarios(7,spec)['episodes'])
  self.assertEqual(len({r['id'] for r in rows}),64)
  for i in range(0,64,4):
   group=rows[i:i+4]
   self.assertEqual(len({r['required_apex_m'] for r in group}),1)
   self.assertEqual([r['goal_forward_m'] for r in group],spec['evaluation_forward_m'])
   for r in group:self.assertEqual(r['foot_offsets_xy_m'],[[r['goal_forward_m'],0.]]*4)
 def test_invalid_requests(self):
  for count,levels in [(0,[0]),(1001,[0]),(4,[]),(4,[-.1]),(4,[float('nan')])]:
   with self.assertRaises(ValueError):directed_jump_scenarios(count,{'evaluation_forward_m':levels,'apex_range_m':[.04,.06]})
