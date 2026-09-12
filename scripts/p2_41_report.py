"""Validate instrumentation against existing fixed-policy first episodes."""
import json
from pathlib import Path
import numpy as np
from audit_chained_evaluation import check
from p2_34_archive_audit import digest
ROOT=Path(__file__).resolve().parents[1]

def inspect(seed):
    old=ROOT/f'artifacts/p2-40-weighted-seed{seed}__final-evaluation'
    new=ROOT/f'artifacts/p2-41-reward-seed{seed}-retry1'
    check(new)
    read=lambda p,n:json.loads((p/n).read_text())
    assert read(old,'scenarios.json')==read(new,'scenarios.json')
    assert read(old,'evaluation.json')['results']==read(new,'evaluation.json')['results']
    assert read(old,'chain-events.json')==read(new,'chain-events.json')
    with np.load(old/'motion-trace.npz') as a,np.load(new/'motion-trace.npz') as b:
        assert set(a.files)==set(b.files)
        for key in a.files:assert np.array_equal(a[key],b[key],equal_nan=True),key
    summary=read(new,'reward-components.json')
    with np.load(new/'reward-components.npz') as data:
        v=data['components'];r=data['reward'];mask=data['active']
        assert np.allclose(v.sum(axis=-1),r,rtol=2e-6,atol=2e-5)
        sums=(v*mask[:,:,None]).sum(axis=0,dtype=np.float64)
        actual=(r*mask).sum(axis=0,dtype=np.float64)
        for i,e in enumerate(summary['episodes']):
            assert e['steps']==int(mask[:,i].sum())
            assert np.allclose(sums[i],list(e['components'].values()),atol=1e-9,rtol=0)
            assert actual[i]==e['actual_return']
            episode=read(new,'evaluation.json')['results'][i]
            assert e['scenario_id']==episode['scenario_id'] and e['steps']==episode['length']
            assert np.allclose(actual[i],episode['return'],atol=2e-4,rtol=2e-6)
    manifests=list((ROOT/'result').glob('*__'+new.name+'/manifest.json'));assert len(manifests)==1
    p=manifests[0];m=json.loads(p.read_text())
    assert digest(p.parent/m['video'])==m['source_video_sha256']
    event=m['chain_events'];assert digest(p.parent/event['file'])==digest(new/'chain-events.json')==event['sha256']
    replay=read(new,'replay.json');assert len(replay['visible_env_ids'])==len(m['video_episodes'])==64
    assert replay['camera']['framing_side']==4
    return dict(seed=seed,evaluation=str(new.relative_to(ROOT)),matched_episode_results=True,
        matched_all_motion_trace_arrays=True,successes=read(new,'evaluation.json')['successes'],
        max_step_error=summary['max_step_reconstruction_error'],
        mean_components=dict(zip(summary['names'],sums.mean(axis=0).tolist())),
        mean_actual_return=float(actual.mean()),manifest=str(p.relative_to(ROOT)))

if __name__=='__main__':
    result=[inspect(s) for s in (1,3)]
    (ROOT/'docs/p2-41-reward-diagnosis.json').write_text(json.dumps(dict(
        scope='two frozen models; instrumentation equivalence on this evaluation only; grouped dense costs; not causal evidence',results=result),indent=2)+'\n')
    for r in result:print(r)
