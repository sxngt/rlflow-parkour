"""Bounded cross-terrain evaluations, gated on each requested seed completion."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]
CASES=(('p2-24-deck','continuous'),('p2-27-continuous','deck'))
def training_run(source,seed):
    return f'{source}-seed{seed}'+('-retry1' if source=='p2-27-continuous' and seed==2 else '')
def command(seed,source,terrain):
    run=training_run(source,seed);train=f'artifacts/{run}'
    return [sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','240','evaluate',
        '--config',train+'/config.json','--checkpoint',train+'/checkpoint-001600.pt',
        '--out',f'artifacts/p2-27-{run}-on-{terrain}','--episodes','64','--diagnostics',
        '--video','--video-envs','64','--video-camera-side','4','--support-mode',terrain,
        '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
        '--support-matched-material','--support-preserve-goals','--research-tag','phase:P2',
        '--research-tag','step:p2-27-support-training','--research-tag','terrain:'+terrain,
        '--research-tag','purpose:cross-terrain-evaluation']
def worker(seed):
    for source,terrain in CASES:
        c=command(seed,source,terrain);r=subprocess.run(c,cwd=ROOT)
        if r.returncode:return {'seed':seed,'exit_code':r.returncode,'command':c}
    return {'seed':seed,'exit_code':0}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',nargs='+',type=int,choices=range(4),default=list(range(4)))
    args=parser.parse_args()
    if len(set(args.seeds))!=len(args.seeds):parser.error('Duplicate seeds')
    for seed in args.seeds:
        for source,_ in CASES:
            p=ROOT/'artifacts'/training_run(source,seed)
            audit(p);audit(p.with_name(p.name+'__final-evaluation'))
        for source,terrain in CASES:
            c=command(seed,source,terrain);p=ROOT/c[c.index('--out')+1]
            if p.exists() or p.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,args.seeds))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
