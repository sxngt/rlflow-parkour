"""Evaluate all P2-27 parents, then directly train discrete retention forks."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def parent(seed):
    return f'p2-27-continuous-seed{seed}'+('-retry1' if seed==2 else '')

def worker(seed):
    source=f'artifacts/{parent(seed)}';base=[sys.executable,'scripts/run_job.py','--gpu',str(seed)]
    commands=[base+['--timeout','240','evaluate','--config',source+'/config.json',
        '--checkpoint',source+'/checkpoint-001600.pt','--out',f'artifacts/p2-31-parent-seed{seed}-split-mixed',
        '--episodes','64','--diagnostics','--video','--video-envs','64','--video-camera-side','4',
        '--support-mode','split','--support-matched-material','--support-calibration',
        'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json','--evaluation-forward-m','0','.15',
        '--research-tag','phase:P2','--research-tag','step:p2-31-direct-retention',
        '--research-tag','terrain:split','--research-tag','purpose:parent-baseline'],
        base+['--timeout','1800','train','--config','configs/p2-31-mixed.json','--seed',str(seed),
        '--fork-from',source+'/checkpoint-001600.pt','--out',f'artifacts/p2-31-mixed-seed{seed}']]
    for command in commands:
        result=subprocess.run(command,cwd=ROOT)
        if result.returncode:return {'seed':seed,'exit_code':result.returncode,'command':command}
    return {'seed':seed,'exit_code':0}

if __name__=='__main__':
    for seed in range(4):
        audit(ROOT/'artifacts'/parent(seed))
        for name in [f'p2-31-parent-seed{seed}-split-mixed',f'p2-31-mixed-seed{seed}']:
            p=ROOT/'artifacts'/name
            if p.exists() or p.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,range(4)))
    print(json.dumps(results),flush=True);sys.exit(int(any(r['exit_code'] for r in results)))
