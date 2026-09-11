"""Compare the same selected development command across explicitly listed jump runs."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('spec',type=Path);args=parser.parse_args()
 spec=json.loads(args.spec.read_text());conditions=list(dict.fromkeys(r['condition'] for r in spec['runs']))
 sample_index=spec.get('trace_episode_index',0);forward=spec.get('show_forward_trace',False)
 fig,axes=plt.subplots(3 if forward else 2,len(conditions),figsize=(10*len(conditions),10 if forward else 7),squeeze=False);details=[];scenario=None
 for entry in spec['runs']:
  p=ROOT/'artifacts'/entry.get('evaluation_run',entry['run']+'__final-evaluation');m=json.loads((p/'run.json').read_text());r=json.loads((p/'evaluation.json').read_text());manifest=json.loads((p/'scenarios.json').read_text())
  assert m['status']=='SUCCEEDED' and m['config'].get('jump')
  assert [x['scenario_id'] for x in r['results']]==[x['id'] for x in manifest['episodes']]
  if scenario is None:scenario=manifest['episodes'][sample_index]
  else:assert scenario==manifest['episodes'][sample_index],'Representative command differs'
  z0=m['stance_calibration']['root_state'][2];ci=conditions.index(entry['condition'])
  with np.load(p/'motion-trace.npz') as a:
   z=a['root_z']-z0;t=a['time'];pos=a['foot_pos'];valid=a['valid'];target=np.array(m['nominal_foot_xy_m'])+np.array(scenario['foot_offsets_xy_m'])
   mask=valid[:,sample_index];err=np.linalg.norm(pos[:,sample_index,:,:2]-target,axis=-1)
   axes[0,ci].plot(t[mask],z[mask,sample_index]*100,label=f"seed {entry['seed']}")
   axes[1,ci].plot(t[mask],err[mask].max(axis=1)*100,label=f"seed {entry['seed']}")
   if forward:
    x=a['root_xy'][:,sample_index,0]-m['stance_calibration']['root_state'][0]
    axes[2,ci].plot(t[mask],x[mask]*100,label=f"seed {entry['seed']}")
   last=[np.flatnonzero(valid[:,i])[-1] for i in range(valid.shape[1])]
   terminal=np.array([z[k,i] for i,k in enumerate(last)])
   details.append({'run':entry['run'],'condition':entry['condition'],'seed':entry['seed'],'mean_terminal_base_rise_m':float(terminal.mean()),'terminal_height_outside_tolerance':int((np.abs(terminal)>m['config']['jump']['final_height_error_max_m']).sum())})
  axes[0,ci].set_title(f"{entry['condition']}: {scenario['id']}")
  axes[0,ci].axhspan(-100*m['config']['jump']['final_height_error_max_m'],100*m['config']['jump']['final_height_error_max_m'],color='green',alpha=.025)
 for ci in range(len(conditions)):
  axes[0,ci].set_ylabel('Base rise [cm]')
  axes[1,ci].axhline(100*m['config']['jump']['landing_radius_m'],color='black',ls='--',label='target radius')
  axes[1,ci].set_ylabel('Maximum foot XY error [cm]');axes[1,ci].set_xlabel('Simulation time [s]')
  if forward:
   axes[2,ci].axhline(100*scenario['goal_forward_m'],color='black',ls='--',label='command')
   axes[2,ci].set_ylabel('Base forward offset from reset [cm]');axes[2,ci].set_xlabel('Simulation time [s]')
  for ax in axes[:,ci]:ax.grid(alpha=.2);ax.legend(ncol=3)
 fig.suptitle('Same development command; original physics samples until first episode ends')
 fig.tight_layout();stem=spec['report'];fig.savefig(ROOT/f'docs/figures/{stem}-jump-trace.png',dpi=160);plt.close(fig)
 (ROOT/f'docs/{stem}-height-diagnosis.json').write_text(json.dumps(details,indent=2)+'\n');print(json.dumps(details))
if __name__=='__main__':main()
