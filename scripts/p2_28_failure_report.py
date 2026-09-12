"""Original-trace distance gates and preflight support in counterfactual gaps."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for seed in range(4):
 for mode in ('continuous','split'):
  p=ROOT/'artifacts'/f'p2-28-material-{mode}-seed{seed}'
  e=json.loads((p/'evaluation.json').read_text())
  with np.load(p/'motion-trace.npz') as a:
   distances=[x['flight_forward_m'] for x in e['results'] if x['flight_touch_recorded']]
   rows.append({'seed':seed,'mode':mode,'travel_met':sum(x['travel_requirement_met'] for x in e['results']),
    'stabilized':sum(x['stabilized_once'] for x in e['results']),'nonfoot_collision':sum(x['nonfoot_collision'] for x in e['results']),
    'example_end_s':float(a['time'][a['valid'][:,0]][-1]),'mean_flight_forward_m':float(np.mean(distances)) if distances else None})
split=json.loads((ROOT/'artifacts/p2-28-material-split-seed0/terrain.json').read_text())
observations=[]
with np.load(ROOT/'artifacts/p2-28-material-continuous-seed0/motion-trace.npz') as a:
 for i in range(64):
  feet=[]
  for j,name in enumerate(split['foot_names']):
   departure=next(s for s in split['layout']['surfaces'] if s['foot']==name and s['role']=='departure')
   landing=next(s for s in split['layout']['surfaces'] if s['foot']==name and s['role']=='landing')
   x,y,z=a['foot_pos'][:,i,j].T;b=departure['bounds_xy_m'];force=np.linalg.norm(a['force'][:,i,j],axis=-1)
   mask=a['valid'][:,i]&(a['stage'][:,i]==0)&(force>5)&(abs(z-.02)<=.01)&(x>b[1])&(x<landing['bounds_xy_m'][0])&(y>b[2])&(y<b[3])
   ix=np.flatnonzero(mask);feet.append({'foot':name,'first_supported_gap_center_s':float(a['time'][ix[0]]) if len(ix) else None})
  observations.append({'episode_index':i,'feet':feet})
payload={'rows':rows,'seed0_continuous_support_in_split_gap_before_flight':observations,
 'scope':'Gap-center projection with >5N force on continuous, not exact contact-pair identity or proof that sphere is fully within gap. Counterfactual geometry diagnostic; not sole causal attribution.'}
(ROOT/'docs/p2-28-failure-diagnosis.json').write_text(json.dumps(payload,indent=2)+'\n')
print('preflight_gap_support_episodes',sum(any(f['first_supported_gap_center_s'] is not None for f in x['feet']) for x in observations))
