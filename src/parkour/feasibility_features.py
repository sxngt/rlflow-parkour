"""Translation-invariant, body-frame features for one four-surface candidate."""
import math

FEATURE_CONTRACT='airborne_body_frame_four_surface_v1'
def rotation(q):
 w,x,y,z=q;n=math.sqrt(sum(v*v for v in q));w,x,y,z=[v/n for v in (w,x,y,z)]
 return [[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)],
         [2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)],
         [2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)]]
def features(context,label):
 state=context['state']['state'];root=state['root_state_local'];R=rotation(root[3:7]);surfaces=context['terrain']['layout']['surfaces']
 def body(v):return [sum(R[j][i]*v[j] for j in range(3)) for i in range(3)]
 def point(p):return body([p[j]-root[j] for j in range(3)])
 out=body(root[7:10])+body(root[10:13])+body([0.,0.,-1.])+state['joint_position']+[v*.05 for v in state['joint_velocity']]+state['environment']['actions']
 targets=state['progress']['target'];out+=[targets[0]-targets[1]]+[min(float(v)*.02,2.) for v in state['progress']['age']]
 plan=state['target_plan'];offset=label['offset_surface_xy_m']
 for pair in range(2):
  for p in plan[pair][targets[pair]]:out+=point(p)
 for index in range(label['start_surface'],label['start_surface']+4):
  surface=surfaces[index];Rs=surface['rotation_local_to_world'];shift=[sum(Rs[j][k]*offset[k] for k in range(2)) for j in range(3)]
  for pair in range(2):
   for p in plan[pair][index]:out+=point([p[j]+shift[j] for j in range(3)])
  out+=body(surface['normal'])+surface['usable_half_extents_m']
 if not all(math.isfinite(v) for v in out):raise ValueError('Nonfinite feasibility feature')
 return out
