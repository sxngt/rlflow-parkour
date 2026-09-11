"""Synthetic simulator contract checks; teleportation is not learned jumping."""
import sys,json,os,traceback
def fatal(typ,exc,tb):
 traceback.print_exception(typ,exc,tb);sys.stderr.flush();os._exit(1)
sys.excepthook=fatal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import launch_app
launch_app(False)
import torch
from parkour.learning import make_env
c=json.loads(Path('configs/p2-01-flat-jump.json').read_text());c['num_envs']=8
e=make_env(c);e.reset();assert e._get_observations()['policy'].shape==(8,66)
zero=torch.zeros(8,12,device=e.device)
for i in range(60):
 _,_,term,trunc,extra=e.step(zero)
 assert not term.any() and not extra['terminal_metrics']['valid_flight'].any()
# A synthetic high airborne state moving upwards verifies the actual sensor gate.
e.reset();root=e.robot.data.root_state_w.clone();root[:,2]+=0.3;root[:,7:]=0;root[:,9]=.8
e.robot.write_root_pose_to_sim(root[:,:7]);e.robot.write_root_velocity_to_sim(root[:,7:]);e.episode_length_buf[:]=30
for i in range(3):
 _,_,term,trunc,extra=e.step(zero)
assert extra['terminal_metrics']['valid_flight'].all(),'Rising separated state not detected'
assert not extra['terminal_metrics']['success'].any(),'Airborne state incorrectly counted as landed'
# Synthetic supported landing with an already verified flight validates final hold.
e.reset();e.flight_seen[:]=True;e.landed[:]=True;e.touched[:]=True;e.apex[:]=.08;e.required_apex[:]=.04;e.episode_length_buf[:]=30
seen=False
for i in range(20):
 _,_,term,trunc,extra=e.step(zero)
 if term.any():
  assert i>=9
  assert extra['terminal_metrics']['success'][term].all()
  seen=True;break
assert seen,'Supported final hold did not finish'
print('PASS: observation shape, standing rejection, rising flight, no airborne success, final hold.',flush=True)
os._exit(0)
