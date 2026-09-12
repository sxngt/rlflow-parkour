"""Frozen-policy airborne reach probe on a wide support deck."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
def worker(seed):
    source=f'artifacts/p3-08-mapped-seed{seed}';out=f'artifacts/p3-14-reach-seed{seed}'
    command=[sys.executable,'scripts/run_job.py','--gpu',str(seed),'--timeout','300','evaluate',
        '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
        '--chain-hops','1','--support-mode','deck','--support-matched-material',
        '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
        '--evaluation-forward-m','.15','.20','.25','.30','--episodes','64','--diagnostics','--video',
        '--video-envs','64','--video-camera-side','4','--research-tag','phase:P3',
        '--research-tag','step:p3-14-reach-envelope']
    code=subprocess.run(command,cwd=ROOT).returncode
    if code:return {'seed':seed,'exit_code':code}
    check(ROOT/out);report=json.loads((ROOT/out/'evaluation.json').read_text())
    return {'seed':seed,'exit_code':0,'successes':report['successes'],'by_distance':report['by_distance']}
if __name__=='__main__':
    for seed in (1,2):
        p=ROOT/f'artifacts/p3-14-reach-seed{seed}'
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt')
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,(1,2)))
    (ROOT/'docs/p3-14-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results),flush=True)
    sys.exit(int(any(x['exit_code'] for x in results)))
