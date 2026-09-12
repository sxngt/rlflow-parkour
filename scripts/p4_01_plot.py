"""Export standalone friction diagnostics; no sensor/causal claims inferred."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    report=json.loads((ROOT/'docs/p4-01-comparison.json').read_text())
    out=ROOT/'artifacts/p4-01-analysis';out.mkdir(exist_ok=True)
    fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
    for column,seed in enumerate((1,2)):
        rows=[x for x in report['evaluations'] if x['seed']==seed]
        axes[0,column].bar([str(x['authored_later_pad_friction']) for x in rows], [100*x['successes']/64 for x in rows],color=['#3b82f6','#e99f35','#dd5566'])
        axes[0,column].set(title=f'Seed {seed}: eight-hop completion',xlabel='Authored later-pad friction',ylabel='Success (%)',ylim=(0,105))
        for row,color in zip(rows,['#3b82f6','#e99f35','#dd5566']):
            values=[None if x['supported_motion_m_per_foot_second'] is None else 1000*x['supported_motion_m_per_foot_second'] for x in row['segments']]
            axes[1,column].plot(range(1,9),values,'o-',label=str(row['authored_later_pad_friction']),color=color)
        axes[1,column].axvline(3.5,color='gray',linestyle='--')
        axes[1,column].set(title='Supported foot-center motion (not proven slip)',xlabel='Hop (material change at landing 4)',ylabel='Travel / supported foot time (mm/s)')
        axes[1,column].legend(title='Pad friction')
    fig.suptitle('P4-01 fixed-policy sensitivity | 64 development cases per condition\nDifferent survival changes exposure; authored friction is not effective contact friction',fontsize=12)
    fig.savefig(out/'friction-completion-and-supported-motion.png',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(10,7),sharex=True,constrained_layout=True)
    sources=[('0.5','p3-11-mapped-seed2-hops8'),('0.2','p4-01-mapped-seed2-friction0p2'),('0.05','p4-01-mapped-seed2-friction0p05')]
    for label,name in sources:
        with np.load(ROOT/'artifacts'/name/'motion-trace.npz') as z:a={k:z[k] for k in z.files}
        mask=a['valid'][:,0]&(a['segment'][:,0]==3)
        time=a['time'][mask];time=time-time[0]
        errors=np.linalg.norm(a['foot_pos'][mask,0,:,:2]-a['target_xy'][mask,0],axis=-1)
        axes[0].plot(time,errors.max(axis=1)*100,label=label)
        axes[1].plot(time,np.maximum(a['force'][mask,0,:,2],0).min(axis=1),label=label)
    axes[0].axhline(5,color='gray',linestyle='--',label='Legacy XY radius')
    axes[0].set(ylabel='Worst foot-center target error (cm)',title='Seed 2, scenario 20000, fourth hop only')
    axes[1].set(ylabel='Minimum normal force over four feet (N)',xlabel='Seconds since fourth-hop start')
    axes[0].legend(title='Authored pad friction');axes[1].legend()
    fig.suptitle('Representative trajectory, not a population confidence interval\nMapped contact additionally requires each intended surface and simultaneous support',fontsize=12)
    fig.savefig(out/'representative-fourth-hop.png',dpi=180)
    (out/'manifest.json').write_text(json.dumps({'source_comparison':'docs/p4-01-comparison.json','figures':['friction-completion-and-supported-motion.png','representative-fourth-hop.png'],'scope':'Descriptive diagnostics; no unique failure cause or measured effective friction claim'},indent=2)+'\n')
