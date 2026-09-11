import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
fig,axes=plt.subplots(2,1,figsize=(10,7));details=[]
for seed in range(4):
 p=Path(f'artifacts/p2-01-jump-seed{seed}__final-evaluation');m=json.loads((p/'run.json').read_text());r=json.loads((p/'evaluation.json').read_text());z0=m['stance_calibration']['root_state'][2]
 with np.load(p/'motion-trace.npz') as a:
  z=a['root_z']-z0; t=a['time'];pos=a['foot_pos'];valid=a['valid'];nom=np.array(m['nominal_foot_xy_m']);err=np.linalg.norm(pos[:,:,:,:2]-nom,axis=-1)
  axes[0].plot(t,z[:,0]*100,label=f'seed {seed}');axes[1].plot(t,err[:,0].max(axis=1)*100,label=f'seed {seed}')
  details.append({'seed':seed,'mean_terminal_base_rise_m':float(z[-1].mean()),'terminal_height_outside_6cm':int((np.abs(z[-1])>.06).sum())})
axes[0].axhspan(-6,6,color='green',alpha=.1,label='final height tolerance');axes[0].set_ylabel('Base rise [cm]');axes[0].set_ylim(-13,9)
axes[1].axhline(5,color='black',ls='--',label='target radius');axes[1].set_ylabel('Maximum foot XY error [cm]');axes[1].set_xlabel('Simulation time [s]')
for ax in axes:ax.grid(alpha=.2);ax.legend(ncol=3)
fig.suptitle('P2-01: same development command 20000, all four training seeds');fig.tight_layout();fig.savefig('docs/figures/p2-01-jump-trace.png',dpi=160)
Path('docs/p2-01-height-diagnosis.json').write_text(json.dumps(details,indent=2)+'\n');print(details)
