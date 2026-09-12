import copy,unittest,math
from parkour.feasibility_features import features
class FeatureTests(unittest.TestCase):
 def fixture(self):
  plan=[[[[float(s),float(f),.02] for f in (-.1,.1)] for s in range(7)] for pair in range(2)]
  state={'root_state_local':[.2,.3,.4,1.,0.,0.,0.,1.,2.,3.,.1,.2,.3],'joint_position':[0.]*12,'joint_velocity':[0.]*12,
   'environment':{'actions':[0.]*12},'progress':{'target':[1,0],'age':[2,3]},'target_plan':plan}
  surfaces=[{'rotation_local_to_world':[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],'normal':[0.,0.,1.],'usable_half_extents_m':[.3,.3]} for _ in range(7)]
  return {'state':{'state':state},'terrain':{'layout':{'surfaces':surfaces}}},{'offset_surface_xy_m':[.08,.04],'start_surface':2}
 def test_global_translation_does_not_leak_map_position(self):
  c,l=self.fixture();original=features(c,l);state=c['state']['state'];state['root_state_local'][0]+=20
  for pair in state['target_plan']:
   for feet in pair:
    for p in feet:p[0]+=20
  self.assertTrue(all(abs(a-b)<1e-12 for a,b in zip(original,features(c,l))))
 def test_global_yaw_invariance(self):
  c,l=self.fixture();original=features(c,l);s=c['state']['state']
  def turn(v):return [-v[1],v[0],v[2]]
  root=s['root_state_local'];root[:3]=turn(root[:3]);root[3:7]=[math.sqrt(.5),0.,0.,math.sqrt(.5)];root[7:10]=turn(root[7:10]);root[10:13]=turn(root[10:13])
  for pair in s['target_plan']:
   for feet in pair:
    for p in feet:p[:]=turn(p)
  for surface in c['terrain']['layout']['surfaces']:surface['rotation_local_to_world']=[[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]
  self.assertTrue(all(abs(a-b)<1e-12 for a,b in zip(original,features(c,l))))
