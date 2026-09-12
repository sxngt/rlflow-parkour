"""Cross-terrain and mixed-distance regression evaluations for P2-29 forks."""
from concurrent.futures import ThreadPoolExecutor
import argparse,json
from pathlib import Path
import subprocess,sys
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]
def commands(seed):
    for mode in ('continuous','split'):
        train=f'artifacts/p2-29-{mode}-seed{seed}'
        for terrain,regression in [(('split' if mode=='continuous' else 'continuous'),False),('continuous',True)]:
            out=f'{train}-'+('regression' if regression else f'on-{terrain}')
            c=[sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','240','evaluate',
               '--config',train+'/config.json','--checkpoint',train+'/checkpoint-000800.pt','--out',out,
               '--episodes','64','--diagnostics','--video','--video-envs','64','--video-camera-side','4',
               '--support-mode',terrain,'--support-matched-material','--support-calibration',
               'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json','--research-tag','phase:P2',
               '--research-tag','step:p2-29-support-finetuning','--research-tag','terrain:'+terrain,
               '--research-tag','purpose:'+('regression' if regression else 'cross-terrain')]
            if regression:c+=['--evaluation-forward-m','0','.05','.1','.15']
            yield c
def worker(seed):
    for c in commands(seed):
        r=subprocess.run(c,cwd=ROOT)
        if r.returncode:return {'seed':seed,'exit_code':r.returncode,'command':c}
    return {'seed':seed,'exit_code':0}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',nargs='+',type=int,choices=range(4),default=list(range(4)));args=p.parse_args()
    if len(set(args.seeds))!=len(args.seeds):p.error('Duplicate seeds')
    for seed in args.seeds:
        for mode in ('continuous','split'):
            path=ROOT/'artifacts'/f'p2-29-{mode}-seed{seed}';audit(path);audit(path.with_name(path.name+'__final-evaluation'))
        for c in commands(seed):
            path=ROOT/c[c.index('--out')+1]
            if path.exists() or path.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {path}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,args.seeds))
    print(json.dumps(results),flush=True);sys.exit(int(any(r['exit_code'] for r in results)))
