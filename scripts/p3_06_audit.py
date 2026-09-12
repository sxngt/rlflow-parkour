"""Compare restored remaining-hop physics with original continuation."""
import json
from pathlib import Path
import numpy as np
from audit_artifacts import audit,digest
ROOT=Path(__file__).resolve().parents[1]


def compare():
    p=ROOT/'artifacts/p3-06-restored-seed1';old=ROOT/'artifacts/p3-05-transition-states-seed1'
    audit(p)
    read=lambda d,n:json.loads((d/n).read_text())
    meta=read(p,'transition-restore.json');report=read(p,'evaluation.json');original=read(old,'evaluation.json')
    assert report['course_successes'] is None and report['evaluation_scope']=='restored_remaining_hop_only'
    assert meta['snapshot_sha256']==digest(old/'transition-states.npz')
    rows=[]
    with np.load(p/'motion-trace.npz') as a,np.load(old/'motion-trace.npz') as b:
        for i,start in enumerate(meta['source_episode_steps']):
            length=report['results'][i]['length']-start
            assert int(a['valid'][:,i].sum())==4*length
            common=min(length,original['results'][i]['length']-start)*4
            assert common>=4
            row={'env':i,'source_step':start,'restored_remaining_steps':length,
                 'original_remaining_steps':original['results'][i]['length']-start,
                 'original_failure':original['results'][i]['failure'], 'restored_failure':report['results'][i]['failure']}
            for label,n in [('first_control_step',4),('preparation',min(common,60)),('common_segment',common)]:
                values={}
                for key in ('root_xy','root_z','foot_pos','force','action','nonfoot_peak'):
                    x=a[key][:n,i];y=b[key][start*4:start*4+n,i]
                    values[key+'_max_abs_diff']=float(np.max(np.abs(x-y)))
                row[label]=values
            rows.append(row)
    ranges={label:{k:max(row[label][k] for row in rows) for k in rows[0][label]}
            for label in ('first_control_step','preparation','common_segment')}
    result={'initial_observation_max_abs_error':meta['initial_observation_max_abs_error'],
            'restored_remaining_hop_successes':report['successes'],'course_successes':None,
            'scope':'Restore probe only. Divergence is measured, not assumed acceptable for training resets.',
            'maximum_errors_across_environments':ranges,'rows':rows}
    (ROOT/'docs/p3-06-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':compare()
