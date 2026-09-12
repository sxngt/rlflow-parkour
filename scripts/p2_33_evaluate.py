"""P2-33: held last joint target during inter-hop preparation."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]

def worker(seed):
    source=f'artifacts/p2-31-mixed-seed{seed}'
    command=[sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','240','evaluate',
        '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt',
        '--out',f'artifacts/p2-33-hold-last-seed{seed}','--support-mode','deck','--support-matched-material',
        '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
        '--chain-hops','2','--chain-settle-mode','hold-last','--episodes','64','--diagnostics','--video','--video-envs','64','--video-camera-side','4',
        '--research-tag','phase:P2','--research-tag','step:p2-33-settle-command',
        '--research-tag','terrain:deck','--research-tag','purpose:chained-execution']
    r=subprocess.run(command,cwd=ROOT)
    return {'seed':seed,'exit_code':r.returncode}

if __name__=='__main__':
    for seed in range(4):
        audit(ROOT/'artifacts'/f'p2-31-mixed-seed{seed}')
        p=ROOT/'artifacts'/f'p2-33-hold-last-seed{seed}'
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError(f'Existing attempt {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,range(4)))
    print(json.dumps(results),flush=True);sys.exit(int(any(r['exit_code'] for r in results)))
