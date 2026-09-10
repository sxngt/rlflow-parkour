"""Synthetic state-machine checks, not a policy performance evaluation."""
import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import launch_app
launch_app(False)
import torch
from parkour.learning import make_env
cfg=json.loads(Path('configs/p1-step02-stable-a.json').read_text());cfg['num_envs']=4
e=make_env(cfg);e.reset()
e.stage[:]=3;e.phase[:]=1;e.place_event[:]=True;e.lift_event[:]=False;e.reset_buf[:]=False;e.reset_time_outs[:]=False;e.failure[:]=False;e.success[:]=False
e._get_rewards()
assert (e.stage==4).all() and (e.phase==1).all()
e.reset();e.stage[:]=4;e.phase[:]=1;e.targets[:]=e.robot.data.body_pos_w[:,e.foot_ids]
seen=False
for step in range(12):
 _,_,term,trunc,extras=e.step(torch.zeros(4,12,device=e.device))
 if term.any():
  assert step>=9
  assert extras['terminal_metrics']['success'][term].all()
  assert (extras['terminal_metrics']['completed_contacts'][term]==4).all()
  seen=True;break
assert seen,'Final stabilization not reached in synthetic supported stance'
print('PASS: fourth placement advances to stabilization; success waits >=10 control steps.',flush=True)
os._exit(0)
