"""Evaluate frozen mapped policies on six/eight-hop geometric courses."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def worker(item):
    seed,friction,gpu=item
    hops=8
    condition="mapped"
    source=f'artifacts/p3-08-{condition}-seed{seed}'
    out=f'artifacts/p4-01-mapped-seed{seed}-friction'+str(friction).replace('.', 'p')
    cmd=[sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','300','evaluate',
         '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
         '--chain-hops',str(hops),'--chain-settle-mode','hold-last','--support-mode','course','--support-matched-material',
         '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
         '--course-friction',str(friction),'--friction-start-station','4','--map-goal-forward-m',str(.15*hops),'--mapped-contact-progress','--map-course-boundary','--episodes','64','--diagnostics','--video',
         '--video-envs','64','--video-camera-side','4','--research-tag','phase:P4',
         '--research-tag','step:p4-01-spatial-friction','--research-tag','condition:'+condition]
    code=subprocess.run(cmd,cwd=ROOT).returncode
    if code:return dict(condition=condition,seed=seed,hops=hops,friction=friction,exit_code=code)
    checked=check(ROOT/out)
    r=json.loads((ROOT/out/'evaluation.json').read_text())
    return dict(condition=condition,seed=seed,hops=hops,friction=friction,exit_code=0,successes=r['successes'],
                completed_hops_histogram=r['completed_hops_histogram'],audit=checked)


if __name__=='__main__':
    low_only = '--low-only' in sys.argv
    prior=json.loads((ROOT/'docs/p3-08-comparison.json').read_text())
    assert len(prior['evaluations'])==18 and prior['new_training_steps']==78643200
    # The preceding pipeline performed full artifact audits; retain its evidence.
    plan=[(1,.2,0),(2,.2,1),(1,.05,2),(2,.05,3)]
    if low_only: plan = [item for item in plan if item[1] == .05]
    for s,f,g in plan:
        p=ROOT/(f'artifacts/p4-01-mapped-seed{s}-friction'+str(f).replace('.', 'p'))
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    with ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(worker,plan))
    (ROOT/('docs/p4-01-low-results.json' if low_only else 'docs/p4-01-results.json')).write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in x.items() if k!='audit'} for x in r]),flush=True)
    sys.exit(int(any(x['exit_code'] for x in r)))
