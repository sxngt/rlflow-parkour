"""Synthetic travel contracts, including intentional teleports; not policy results."""
import sys,json,os,traceback
from pathlib import Path
def fatal(typ,exc,tb):
 traceback.print_exception(typ,exc,tb);sys.stderr.flush();os._exit(1)
sys.excepthook=fatal
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import launch_app
launch_app(False)
import torch
from parkour.learning import make_env
c=json.loads(Path('configs/p2-05-directed-jump.json').read_text());c['num_envs']=8
e=make_env(c);e.reset();zero=torch.zeros(8,12,device=e.device)
assert e._get_observations()['policy'].shape==(8,66)
assert ((e.goal_distance>=0)&(e.goal_distance<=.15)).all()
for _ in range(30):
 _,_,term,_,_=e.step(zero)
 assert not term.any() and not e.travel.launched.any()
# An actual upward airborne sensor state outside the allowed launch area is rejected.
e.reset();root=e.robot.data.root_state_w.clone();root[:,0]+=.1;root[:,2]+=.3;root[:,7:]=0;root[:,9]=.8
e.robot.write_root_pose_to_sim(root[:,:7]);e.robot.write_root_velocity_to_sim(root[:,7:]);e.episode_length_buf[:]=30
rejected=False
for _ in range(4):
 _,_,term,_,extra=e.step(zero)
 if term.any():
  m=extra['terminal_metrics'];assert m['failure'][term].all() and not m['launch_in_region'][term].any();rejected=True;break
assert rejected
# Synthetic launch and teleport to the commanded stance validate contact capture and success conjunction.
for distance in (0.,.15):
 e.reset();offset=torch.zeros(8,4,2,device=e.device);offset[:,:,0]=distance;e.set_sequence_offsets(offset)
 start=e.robot.data.root_pos_w[:,:2]-e.scene.env_origins[:,:2]
 e.travel.launch(torch.ones(8,dtype=torch.bool,device=e.device),start,e.calibrated_root[:2],.03)
 e.flight_seen[:]=True;e.apex[:]=.08;e.required_apex[:]=.04;e.episode_length_buf[:]=30
 root=e.robot.data.root_state_w.clone();root[:,0]+=distance;e.robot.write_root_pose_to_sim(root[:,:7])
 finished=False
 for i in range(30):
  _,_,term,_,extra=e.step(zero)
  if term.any():
   m=extra['terminal_metrics'];assert m['success'][term].all() and m['travel_requirement_met'][term].all()
   assert (m['flight_forward_m'][term]-distance).abs().max()<.01
   finished=True;break
 assert finished,f'Synthetic directed stance {distance} did not complete'
print('PASS: sampled goals and observation, standing rejected, launch outside region rejected, zero and forward synthetic landing conjunction.',flush=True)
os._exit(0)
