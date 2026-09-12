"""Check landing snapshots against unchanged original rollout and physics traces."""
import json
from pathlib import Path
import numpy as np
from audit_artifacts import digest
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def audit():
    p=ROOT/'artifacts/p3-05-transition-states-seed1'
    old=ROOT/'artifacts/p3-04-eval-course-seed1-course'
    check(p)
    read=lambda path,name:json.loads((path/name).read_text())
    assert read(p,'evaluation.json')['results']==read(old,'evaluation.json')['results']
    with np.load(p/'motion-trace.npz') as a,np.load(old/'motion-trace.npz') as b:
        assert set(a.files)==set(b.files)
        for key in a.files:assert np.array_equal(a[key],b[key],equal_nan=True),key
    meta=read(p,'transition-states.json');run=read(p,'run.json');events=read(p,'chain-events.json')
    for name in ('transition-states.json','transition-states.npz'):
        assert digest(p/name)==run['artifacts'][name]
    with np.load(p/'transition-states.npz') as a,np.load(p/'motion-trace.npz') as t:
        assert meta['count']==len(events['transitions'])==64
        assert a['root'].shape==(64,13) and a['joint_pos'].shape==a['joint_vel'].shape==(64,12)
        assert len(meta['joint_names'])==12
        assert all(len(a[k])==64 for k in a.files)
        for rec in meta['records']:
            row,i,step=rec['array_row'],rec['env_index'],rec['episode_step'];idx=step*4-1
            event=next(e for e in events['transitions'] if e['env_index']==i)
            assert step==event['episode_step'] and rec['completed_hops']==1
            assert rec['scenario_id']==read(p,'evaluation.json')['results'][i]['scenario_id']
            assert np.allclose(a['root'][row,:2],t['root_xy'][idx,i],atol=1e-7,rtol=0)
            assert np.allclose(a['root'][row,2],t['root_z'][idx,i],atol=1e-7,rtol=0)
            assert np.allclose(a['root'][row,9],t['root_vz'][idx,i],atol=1e-7,rtol=0)
            assert np.array_equal(a['actions'][row],t['action'][idx,i])
            assert np.allclose(a['target_local'][row,:,:2],event['target_xy_m'],atol=2e-6,rtol=0)
            assert np.allclose(np.linalg.norm(a['root'][row,3:7]),1.,atol=1e-5)
        assert all(np.isfinite(a[k]).all() for k in a.files)
    mpath=next((ROOT/'result').glob('*__'+p.name+'/manifest.json'));m=json.loads(mpath.read_text())
    assert digest(mpath.parent/m['video'])==m['source_video_sha256']
    result={'snapshot_count':meta['count'],'episode_results_exact_equal':True,'all_motion_arrays_exact_equal':True,
            'snapshot_trace_boundary_match':True,'artifact_and_video_hashes_verified':True,
            'scope':'read-only capture validated; reset and physics replay not yet validated'}
    (ROOT/'docs/p3-05-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':print(audit())
