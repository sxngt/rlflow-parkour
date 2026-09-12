"""P2-31 continuous regression and retained split jump."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit

ROOT=Path(__file__).resolve().parents[1]


def commands(seed):
    cases=[]
    for mode in ('mixed',):
        train=f'p2-31-{mode}-seed{seed}'
        cases += [(train,train+'-regression','continuous',[0.,.05,.1,.15],'regression'),
                  (train,train+'-split15','split',[.15],'retention')]
    for train,out,terrain,distances,purpose in cases:
        yield [sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','240','evaluate',
            '--config',f'artifacts/{train}/config.json','--checkpoint',f'artifacts/{train}/checkpoint-000800.pt',
            '--out',f'artifacts/{out}','--episodes','64','--diagnostics','--video','--video-envs','64','--video-camera-side','4',
            '--support-mode',terrain,'--support-matched-material','--support-calibration',
            'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
            '--research-tag','phase:P2','--research-tag','step:p2-31-direct-retention',
            '--research-tag','terrain:'+terrain,'--research-tag','purpose:'+purpose,
            '--evaluation-forward-m',*map(str,distances)]


def worker(seed):
    for command in commands(seed):
        result=subprocess.run(command,cwd=ROOT)
        if result.returncode:
            return {'seed':seed,'exit_code':result.returncode,'command':command}
    return {'seed':seed,'exit_code':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,nargs='+',choices=range(4),default=list(range(4)))
    args=parser.parse_args()
    if len(set(args.seeds))!=len(args.seeds):parser.error('Duplicate seeds')
    for seed in args.seeds:
        audit(ROOT/'artifacts'/f'p2-29-split-seed{seed}')
        for mode in ('mixed',):
            path=ROOT/'artifacts'/f'p2-31-{mode}-seed{seed}'
            audit(path);audit(path.with_name(path.name+'__final-evaluation'))
        for command in commands(seed):
            path=ROOT/command[command.index('--out')+1]
            if path.exists() or path.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {path}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,args.seeds))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
