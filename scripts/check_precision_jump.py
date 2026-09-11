"""Synthetic precision-gate checks; injected flight flags are not policy performance."""
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
c=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else 'configs/p2-03-precise-jump.json').read_text());c['num_envs']=8
e=make_env(c);e.reset();zero=torch.zeros(8,12,device=e.device)
for _ in range(30):
 _,_,term,_,_=e.step(zero)
 assert not term.any() and not e.first_touch.seen.any()
# A bad first touch remains bad even when the actual feet are subsequently aligned.
e.reset();e.flight_seen[:]=True;e.landed[:]=True;e.touched[:]=True;e.apex[:]=.08;e.required_apex[:]=.04;e.episode_length_buf[:]=30
e.first_touch.seen[:]=True;e.first_touch.errors[:]=.2
for _ in range(20):
 _,_,term,_,extra=e.step(zero)
 assert not term.any(),'Incorrect first contact accepted after later stabilization'
assert e.stabilized.all() and not e.first_touch.within(.05).any()
# Read actual contact samples at supported stance after a synthetic flight flag.
e.reset();e.flight_seen[:]=True;e.apex[:]=.08;e.required_apex[:]=.04;e.episode_length_buf[:]=30
finished=False
for i in range(20):
 _,_,term,_,extra=e.step(zero)
 if i==0:
  assert e.first_touch.seen.all() and e.first_touch.within(.05).all()
  assert (e.first_touch_bonus>0).all()
 if i==1:assert e.first_touch_bonus.eq(0).all(),'Repeated reward for same contact'
 if term.any():
  assert i>=9
  assert extra['terminal_metrics']['success'][term].all()
  assert extra['terminal_metrics']['first_touch_all_within'][term].all()
  finished=True;break
assert finished
print('PASS: standing rejected; bad first touch cannot be repaired; actual physics contact captured; bonus once; precise hold succeeds.',flush=True)
os._exit(0)
