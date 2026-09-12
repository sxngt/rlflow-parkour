"""Extend the completed policies to a four-hop mapped-contact course."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def worker(item):
    condition,seed,gpu=item
    source=f'artifacts/p3-08-{condition}-seed{seed}'
    out=f'artifacts/p3-09-{condition}-seed{seed}'
    cmd=[sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','300','evaluate',
         '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
         '--chain-hops','4','--chain-settle-mode','hold-last','--support-mode','course','--support-matched-material',
         '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
         '--map-goal-forward-m','.60','--mapped-contact-progress','--episodes','64','--diagnostics','--video',
         '--video-envs','64','--video-camera-side','4','--research-tag','phase:P3',
         '--research-tag','step:p3-09-four-hop-course','--research-tag','condition:'+condition]
    code=subprocess.run(cmd,cwd=ROOT).returncode
    if code:return dict(condition=condition,seed=seed,exit_code=code)
    checked=check(ROOT/out)
    r=json.loads((ROOT/out/'evaluation.json').read_text())
    return dict(condition=condition,seed=seed,exit_code=0,successes=r['successes'],
                completed_hops_histogram=r['completed_hops_histogram'],audit=checked)


if __name__=='__main__':
    prior=json.loads((ROOT/'docs/p3-08-comparison.json').read_text())
    assert len(prior['evaluations'])==18 and prior['new_training_steps']==78643200
    # The preceding pipeline performed full artifact audits; retain its evidence.
    plan=[('mapped',1,0),('strict',1,1),('mapped',2,2),('strict',2,3)]
    for c,s,g in plan:
        p=ROOT/f'artifacts/p3-09-{c}-seed{s}'
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    with ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(worker,plan))
    (ROOT/'docs/p3-09-results.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in x.items() if k!='audit'} for x in r]),flush=True)
    sys.exit(int(any(x['exit_code'] for x in r)))
