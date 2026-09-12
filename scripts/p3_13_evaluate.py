"""Frozen-policy pilot for explicit launch/landing support heights."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def worker(item):
    seed,pattern,gpu=item
    heights={'zero':[0.]*9,'up':[0.,0.,.01,.01,0.,0.,.01,.01,0.],
             'down':[0.,0.,-.01,-.01,0.,0.,-.01,-.01,0.]}[pattern]
    source=f'artifacts/p3-08-mapped-seed{seed}'
    out=f'artifacts/p3-13-mapped-seed{seed}-{pattern}'
    command=[sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','300','evaluate',
        '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
        '--chain-hops','8','--chain-settle-mode','hold-last','--support-mode','course','--support-matched-material',
        '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
        '--course-station-heights',*map(str,heights),'--map-goal-forward-m','1.2',
        '--mapped-contact-progress','--map-course-boundary','--episodes','64','--diagnostics','--video',
        '--video-envs','64','--video-camera-side','4','--research-tag','phase:P3',
        '--research-tag','step:p3-13-height-course','--research-tag','condition:'+pattern]
    code=subprocess.run(command,cwd=ROOT).returncode
    if code:return dict(seed=seed,pattern=pattern,exit_code=code)
    check(ROOT/out)
    result=json.loads((ROOT/out/'evaluation.json').read_text())
    return dict(seed=seed,pattern=pattern,exit_code=0,successes=result['successes'],completed_hops_histogram=result['completed_hops_histogram'])


if __name__=='__main__':
    plan=[(2,'zero',0),(1,'up',1),(2,'up',2),(2,'down',3)]
    for seed,pattern,gpu in plan:
        path=ROOT/f'artifacts/p3-13-mapped-seed{seed}-{pattern}'
        if path.exists() or path.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(path))
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,plan))
    (ROOT/'docs/p3-13-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results),flush=True)
    sys.exit(int(any(x['exit_code'] for x in results)))
