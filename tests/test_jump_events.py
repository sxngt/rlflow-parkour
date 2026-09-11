import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from parkour.jump_events import jump_transition
from parkour.scenarios import jump_scenarios

class JumpTests(unittest.TestCase):
 def args(self):
  t=lambda x:torch.tensor([x])
  spec={'flight_min_rise_m':.03,'flight_min_vz_m_s':.2,'landing_radius_m':.05,'final_vz_max_m_s':.15,
   'final_angular_speed_max_rad_s':1.,'final_height_error_max_m':.06,'final_hold_seconds':.2}
  return dict(seen=t(False),landed=t(False),touched=torch.zeros(1,4,dtype=torch.bool),contact=torch.ones(1,4,dtype=torch.bool),
   air_window=t(False),settled=t(True),rise=t(.04),vz=t(0.),errors=torch.zeros(1,4),apex=t(.06),required_apex=t(.05),
   angular_speed=t(0.),height_error=t(0.),history_supported=t(True),failure=t(False),hold=t(0),dt=.02,spec=spec)
 def test_standing_cannot_complete_jump(self):
  a=self.args();out=jump_transition(**a)
  self.assertFalse(out[0].item());self.assertFalse(out[-1].item())
 def test_flight_requires_settled_ascending_and_air_history(self):
  a=self.args();a.update(air_window=torch.tensor([True]),contact=torch.zeros(1,4,dtype=torch.bool),vz=torch.tensor([.3]))
  self.assertTrue(jump_transition(**a)[4].item())
  for key,value in [('settled',False),('air_window',False),('vz',-.3),('rise',.01),('failure',True)]:
   b={**a,key:torch.tensor([value])};self.assertFalse(jump_transition(**b)[4].item(),key)
 def test_landing_needs_hold_and_touch_is_one_shot(self):
  a=self.args();a['seen']=torch.tensor([True])
  for i in range(10):
   out=jump_transition(**a)
   self.assertEqual(out[5].sum().item(),4 if i==0 else 0)
   self.assertEqual(out[-1].item(),i==9)
   a.update(seen=out[0],landed=out[1],touched=out[2],hold=out[3])
  a['failure']=torch.tensor([True]);self.assertFalse(jump_transition(**a)[-1].item())
 def test_apex_and_support_are_required(self):
  a=self.args();a.update(seen=torch.tensor([True]),hold=torch.tensor([20]))
  a['apex']=torch.tensor([.03]);self.assertEqual(jump_transition(**a)[3].item(),0)
  a['apex']=torch.tensor([.06]);a['history_supported']=torch.tensor([False]);self.assertEqual(jump_transition(**a)[3].item(),0)
 def test_commands_are_reproducible_and_inside_bounds(self):
  a=jump_scenarios(64,{'apex_range_m':[.04,.06]})
  self.assertEqual(a['episodes'][:4],jump_scenarios(4,{'apex_range_m':[.04,.06]})['episodes'])
  self.assertTrue(all(.04<=e['required_apex_m']<=.06 for e in a['episodes']))
