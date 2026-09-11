"""Bounded mean versus sampled action diagnosis for four frozen policies."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
CASES=[(experiment,rng) for experiment in ('p2-24',) for rng in (20000,20001)]

def worker(seed):
    for experiment,rng in CASES:
        mode='sampled'
        train=f'artifacts/{experiment}-deck-seed{seed}'
        out=f'artifacts/p2-24-{experiment}-seed{seed}-sampled-rng{rng}'
        command=[sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','240','evaluate',
            '--config',train+'/config.json','--checkpoint',train+'/checkpoint-001600.pt','--out',out,
            '--action-mode',mode,'--action-seed',str(rng),'--episodes','64','--diagnostics','--video',
            '--video-envs','64','--video-camera-side','4','--research-tag','phase:P2',
            '--research-tag','step:p2-24-late-noise-reduction','--research-tag','action:'+mode]
        result=subprocess.run(command,cwd=ROOT)
        if result.returncode:return {'out':out,'exit_code':result.returncode}
    return {'seed':seed,'exit_code':0}

if __name__=='__main__':
    from audit_artifacts import audit
    for seed in range(4):
        train=ROOT/'artifacts'/f'p2-24-deck-seed{seed}'
        audit(train)
        audit(train.with_name(train.name+'__final-evaluation'))
    for seed in range(4):
        for experiment,rng in CASES:
            p=ROOT/'artifacts'/f'p2-24-{experiment}-seed{seed}-sampled-rng{rng}'
            if p.exists() or p.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,range(4)))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
