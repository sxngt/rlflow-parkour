"""Locate preflight support-region exits in frozen P2-26 original traces."""
import json
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
rows=[]
for seed in range(4):
 for mode in ('continuous','split'):
  p=ROOT/'artifacts'/f'p2-26-material-{mode}-seed{seed}'
  terrain=json.loads((p/'terrain.json').read_text());ev=json.loads((p/'evaluation.json').read_text())
  with np.load(p/'motion-trace.npz') as z:a={k:z[k] for k in z.files}
  assert ev['episodes']==64 and ev['valid_flights']==0 and np.allclose(np.diff(a['time']),.005)
  details=[]
  for i,e in enumerate(ev['results']):
   valid=a['valid'][:,i].astype(bool);t=a['time'][valid];xyz=a['foot_pos'][valid,i];forces=np.linalg.norm(a['force'][valid,i],axis=-1)
   feet=[]
   for f,name in enumerate(terrain['foot_names']):
    inside=np.zeros(len(t),dtype=bool)
    for surface in terrain['layout']['surfaces']:
     # Union of every real support; do not assume a foot can only contact its named pad.
     x0,x1,y0,y1=surface['bounds_xy_m'];inside|=(xyz[:,f,0]>=x0)&(xyz[:,f,0]<=x1)&(xyz[:,f,1]>=y0)&(xyz[:,f,1]<=y1)
    outside=np.flatnonzero((t>=.3)&~inside)
    low=np.flatnonzero(xyz[:,f,2]<-.02)
    feet.append({'foot':name,'initial_center_inside':bool(inside[0]),'first_xy_exit_s':float(t[outside[0]]) if len(outside) else None,
     'force_at_first_exit_n':float(forces[outside[0],f]) if len(outside) else None,'first_below_top_minus_2cm_s':float(t[low[0]]) if len(low) else None})
   details.append({'scenario_id':e['scenario_id'],'last_observed_s':float(t[-1]),'nonfoot_collision':e['nonfoot_collision'],'feet':feet})
  rows.append({'seed':seed,'mode':mode,'initial_all_inside':sum(all(f['initial_center_inside'] for f in d['feet']) for d in details),
   'any_xy_exit':sum(any(f['first_xy_exit_s'] is not None for f in d['feet']) for d in details),
   'any_below_top_minus_2cm':sum(any(f['first_below_top_minus_2cm_s'] is not None for f in d['feet']) for d in details),
   'nonfoot_collision':sum(d['nonfoot_collision'] for d in details),'details':details})
out={'scope':'Original valid 200Hz samples. XY center within union of all support rectangles; not contact-pair identification or proof of causality. Exit may occur during intended foot lift. No valid jump occurred by the task contract. No additional simulation or learning.', 'rows':rows}
(ROOT/'docs/p2-26-preparation.json').write_text(json.dumps(out,indent=2)+'\n')
for r in rows:print({k:v for k,v in r.items() if k!='details'},'example',r['details'][0])
