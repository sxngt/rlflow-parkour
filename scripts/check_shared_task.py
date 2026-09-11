"""Synthetic shared-foot contract checks; not learned policy performance."""
import sys,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import launch_app
launch_app(False)
import torch
from parkour.learning import make_env
from parkour.scenarios import development_scenarios
c=json.loads(Path('configs/p1-step02e-shared.json').read_text());c['num_envs']=4
e=make_env(c);e.reset();manifest=development_scenarios(4,sequence=c['sequence'])
orders=torch.tensor([x['episode_order_indices'] for x in manifest['episodes']],device=e.device)
offsets=torch.tensor([x['foot_offsets_xy_m'] for x in manifest['episodes']],device=e.device)
e.set_sequence_offsets(offsets,episode_orders=orders)
assert e.active_feet().tolist()==[0,1,2,3]
obs=e._get_observations()['policy'];assert obs[:,61:65].argmax(1).tolist()==[0,1,2,3]
expected=e.scene.env_origins[:,None,:2]+e.nominal_xy
actual=e.targets[:,:,:2]-expected
for i in range(4):
 assert torch.allclose(actual[i,i],offsets[i,i],atol=1e-6)
 for j in range(4):
  if j!=i:assert actual[i,j].abs().max()<1e-6
saved_order=e.episode_order.clone();saved_targets=e.targets.clone()
e._reset_idx(torch.tensor([1],device=e.device))
assert torch.equal(e.episode_order[[0,2,3]],saved_order[[0,2,3]])
assert torch.equal(e.targets[[0,2,3]],saved_targets[[0,2,3]])
e.set_sequence_offsets(offsets,episode_orders=orders)
e.stage[:]=0;e.phase[:]=1;e.place_event[:]=True;e.lift_event[:]=False;e.reset_buf[:]=False;e.reset_time_outs[:]=False;e.failure[:]=False;e.success[:]=False
before=e.targets.clone();e._get_rewards()
assert (e.stage==4).all() and e.active_feet().tolist()==[0,1,2,3]
assert torch.equal(before,e.targets)
assert (e.extras['terminal_metrics']['completed_contacts']==1).all()
print('PASS: per-env active foot, observations, targets, reset isolation, final stage and contact counts.',flush=True)
os._exit(0)
