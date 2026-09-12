"""Eight paired policy forks with balanced terrain order and bounded budgets."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]
def parent(seed):
    return f'p2-27-continuous-seed{seed}'+('-retry1' if seed==2 else '')
def modes(seed):
    return ('continuous','split') if seed%2==0 else ('split','continuous')
def worker(seed):
    for mode in modes(seed):
        out=f'artifacts/p2-29-{mode}-seed{seed}'
        command=[sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','1800','train',
            '--config',f'configs/p2-29-{mode}.json','--seed',str(seed),'--fork-from',
            f'artifacts/{parent(seed)}/checkpoint-001600.pt','--out',out]
        r=subprocess.run(command,cwd=ROOT)
        if r.returncode:return {'seed':seed,'failed_run':out,'exit_code':r.returncode}
    return {'seed':seed,'exit_code':0}
if __name__=='__main__':
    for seed in range(4):
        audit(ROOT/'artifacts'/parent(seed))
        for mode in modes(seed):
            p=ROOT/'artifacts'/f'p2-29-{mode}-seed{seed}'
            if p.exists() or p.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,range(4)))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
