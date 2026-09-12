"""Bounded device-resident telemetry; serialize once after the control episode."""
import torch
FIELDS=(('root',13),('q',12),('dq',12),('target',2),('targets_w',12),('forces',4),('contact_on',4),('actions',12),('accepted',2),('jumps',1))
class ExecutionTrace:
 def __init__(self,max_steps):self.rows=[];self.max_steps=max_steps
 def capture(self,env):
  if len(self.rows)>=self.max_steps:raise RuntimeError('Trace budget exceeded')
  e=env
  self.rows.append(torch.cat([e.robot.data.root_state_w[0],e.robot.data.joint_pos[0],e.robot.data.joint_vel[0],e.progress.target[0],e.targets[0].reshape(-1),e.contacts.data.net_forces_w[0,e.contact_ids,2],e.contact_on[0],e.actions[0],e.progress.accepted[0],e.flights.count[0:1]]).detach())
 def serialize(self):
  if not self.rows:return []
  rows=torch.stack(self.rows).cpu().tolist();result=[]
  for step,values in enumerate(rows):
   out={'step':step};offset=0
   for key,n in FIELDS:
    v=values[offset:offset+n];offset+=n
    if key in ('target','accepted'):v=[int(x) for x in v]
    elif key=='contact_on':v=[bool(x) for x in v]
    elif key=='jumps':v=int(v[0])
    elif key=='targets_w':v=[[v[g*6+f*3:g*6+f*3+3] for f in range(2)] for g in range(2)]
    out[key]=v
   result.append(out)
  return result
