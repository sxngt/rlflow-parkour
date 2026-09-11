"""Bounded mean versus sampled action diagnosis for four frozen policies."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
MODES=[('mean',20000),('sampled',20000),('sampled',20001)]

def worker(seed):
    train=f'artifacts/p2-18-deck-seed{seed}'
    for mode,rng in MODES:
        out=f'artifacts/p2-19-seed{seed}-{mode}-rng{rng}'
        command=[sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','240','evaluate',
            '--config',train+'/config.json','--checkpoint',train+'/checkpoint-001600.pt','--out',out,
            '--action-mode',mode,'--action-seed',str(rng),'--episodes','64','--diagnostics','--video',
            '--video-envs','64','--video-camera-side','4','--research-tag','phase:P2',
            '--research-tag','step:p2-19-action-sampling','--research-tag','action:'+mode]
        result=subprocess.run(command,cwd=ROOT)
        if result.returncode:return {'out':out,'exit_code':result.returncode}
    return {'seed':seed,'exit_code':0}

if __name__=='__main__':
    for seed in range(4):
        for mode,rng in MODES:
            p=ROOT/'artifacts'/f'p2-19-seed{seed}-{mode}-rng{rng}'
            if p.exists() or p.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,range(4)))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
