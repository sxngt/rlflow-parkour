"""P2-29 zero-distance regression gates and seed0 split transfer diagnosis."""
import json
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
post=json.loads((ROOT/'docs/p2-29-regression-post-landing.json').read_text())['rows']
rows=[]
for mode in ('continuous','split'):
 for seed in range(4):
  name=f'p2-29-{mode}-seed{seed}-regression';p=ROOT/'artifacts'/name
  meta=json.loads((p/'run.json').read_text());report=json.loads((p/'evaluation.json').read_text())
  after=next(r for r in post if r['evaluation_run']==name)
  origin=np.asarray(meta['stance_calibration']['root_state'][:2]);details=[]
  with np.load(p/'motion-trace.npz') as a:
   assert np.allclose(np.diff(a['time']),.005)
   for i,r in enumerate(report['results']):
    if abs(r['goal_forward_m'])>1e-6:continue
    valid=a['valid'][:,i];positions=a['root_xy'][valid,i]
    if r['launch_recorded']:
     launch=np.array([r['launch_root_x_m'],r['launch_root_y_m']])
     assert np.linalg.norm(positions-launch,axis=1).min()<1e-5
     displacement=float(np.linalg.norm(launch-origin))
     assert (displacement<=meta['config']['jump']['launch_radius_m'])==bool(r['launch_in_region'])
    else:displacement=None
    if r['success']:gate='success'
    elif not r['valid_flight']:gate='no_valid_flight'
    elif not r['launch_in_region']:gate='outside_launch_region'
    elif not r['first_touch_all_within']:gate='first_touch_not_precise'
    elif not r['stabilized_once']:gate='not_stabilized'
    else:gate='other'
    d=next(d for d in after['details'] if d['scenario_id']==r['scenario_id'])
    details.append({'scenario_id':r['scenario_id'],'gate':gate,'failure':r['failure'],'timeout':r['timeout'],
       'launch_displacement_m':displacement,'terminal_time_s':float(a['time'][valid][-1]),
       'terminal_height_m':float(a['root_z'][valid,i][-1]),
       'final_height_error_m':r['final_height_error_m'],'final_vz_m_s':r['final_vz_m_s'],
       'final_angular_speed_rad_s':r['final_angular_speed_rad_s'],
       'post_landing':d})
  assert len(details)==16
  rows.append({'run':name,'mode':mode,'seed':seed,'gate_counts':dict(Counter(d['gate'] for d in details)),
               'details':details})
p=ROOT/'artifacts/p2-29-continuous-seed0-on-split'
e=json.loads((p/'evaluation.json').read_text())
transfer={'run':p.name,'successes':e['successes'],'failures':sum(r['failure'] for r in e['results']),
 'timeouts':sum(r['timeout'] for r in e['results']),
 'first_touch_precise':e['first_touch_precise_episodes'],'stabilized':e['stabilized_episodes'],
 'per_foot_first_touch_over_5cm':{name:sum(r[f'first_touch_error_{name}_m']>.05 for r in e['results']) for name in ['fl','fr','rl','rr']}}
summary={'zero_distance':rows,'continuous_seed0_split_transfer':transfer,
 'scope':'Earliest unmet recorded gates, not proof of a unique physical cause. Launch XY checked against valid 200Hz trace samples and the calibrated origin. Existing first-touch/post-landing trace audit reused.',
 'additional_training_steps':0}
(ROOT/'docs/p2-29-failure-diagnosis.json').write_text(json.dumps(summary,indent=2)+'\n')
for r in rows:print(r['run'],r['gate_counts'])
print(transfer)
