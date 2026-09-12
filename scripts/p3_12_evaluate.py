"""Evaluate frozen mapped policies on alternating nonuniform eight-hop courses."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def worker(item):
    seed,order,gpu=item
    hops=8
    lengths=([.145,.155] if order=="short-first" else [.155,.145])*4
    condition="mapped"
    source=f'artifacts/p3-08-{condition}-seed{seed}'
    out=f'artifacts/p3-12-mapped-seed{seed}-{order}-retry1'
    cmd=[sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','300','evaluate',
         '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
         '--chain-hops',str(hops),'--chain-settle-mode','hold-last','--support-mode','course','--support-matched-material',
         '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
         '--course-step-lengths',*map(str,lengths),'--map-goal-forward-m',str(sum(lengths)),'--mapped-contact-progress','--map-course-boundary','--episodes','64','--diagnostics','--video',
         '--video-envs','64','--video-camera-side','4','--research-tag','phase:P3',
         '--research-tag','step:p3-12-nonuniform-course','--research-tag','condition:'+condition]
    code=subprocess.run(cmd,cwd=ROOT).returncode
    if code:return dict(condition=condition,seed=seed,hops=hops,order=order,exit_code=code)
    checked=check(ROOT/out)
    r=json.loads((ROOT/out/'evaluation.json').read_text())
    return dict(condition=condition,seed=seed,hops=hops,order=order,exit_code=0,successes=r['successes'],
                completed_hops_histogram=r['completed_hops_histogram'],audit=checked)


if __name__=='__main__':
    prior=json.loads((ROOT/'docs/p3-08-comparison.json').read_text())
    assert len(prior['evaluations'])==18 and prior['new_training_steps']==78643200
    # The preceding pipeline performed full artifact audits; retain its evidence.
    plan=[(1,"short-first",0),(2,"short-first",1),(1,"long-first",2),(2,"long-first",3)]
    for s,o,g in plan:
        p=ROOT/f'artifacts/p3-12-mapped-seed{s}-{o}-retry1'
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    with ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(worker,plan))
    (ROOT/'docs/p3-12-retry1-results.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in x.items() if k!='audit'} for x in r]),flush=True)
    sys.exit(int(any(x['exit_code'] for x in r)))
