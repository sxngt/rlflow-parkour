"""Bounded training-only start-platform pose randomization."""
import math

def validate_jitter(config):
 spec=config.get('reset_jitter')
 if spec is None:return None
 if not isinstance(spec,dict) or set(spec)!={'version','probability','xy_m','yaw_rad'} or spec['version']!='start_pose_jitter_v1':raise ValueError('Invalid start pose jitter contract')
 for key,low,high in [('probability',0.,1.),('xy_m',0.,.05),('yaw_rad',0.,.15)]:
  v=spec[key]
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not low<=v<=high:raise ValueError('Invalid start pose jitter value')
 return dict(spec)

def perturb(root,spec,generator):
 """World XY/yaw only: preserve initial height, roll/pitch, joint pose and velocity."""
 if spec is None:return root
 import torch
 out=root.clone();draw=torch.rand((len(root),4),device=root.device,generator=generator)
 active=draw[:,0]<spec['probability'];out[:,:2]+=(draw[:,1:3]*2-1)*spec['xy_m']*active[:,None]
 yaw=(draw[:,3]*2-1)*spec['yaw_rad']*active;c=torch.cos(yaw/2);s=torch.sin(yaw/2)
 w,x,y,z=root[:,3:7].unbind(1)
 out[:,3:7]=torch.stack((c*w-s*z,c*x-s*y,c*y+s*x,c*z+s*w),1)
 return out

def check_start_margin(layout,calibration,spec):
 start=layout['surfaces'][0]
 if max(abs(a-b) for a,b in zip(start['normal'],[0.,0.,1.]))>1e-6:raise ValueError('Pose jitter requires a horizontal start platform')
 feet=calibration['foot_xy_m'];root=calibration['root_state']
 radius=max(math.hypot(p[0]-root[0],p[1]-root[1]) for p in feet)
 rotation_margin=2*radius*math.sin(spec['yaw_rad']/2)
 for axis in (0,1):
  required=max(abs(p[axis]-start['top_center_m'][axis]) for p in feet)+spec['xy_m']+rotation_margin
  if required>start['usable_half_extents_m'][axis]:raise ValueError('Start pose jitter can leave the safe support region')
