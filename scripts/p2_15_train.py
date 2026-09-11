"""P2-15: eight bounded fresh runs and paired cross-terrain evaluations."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def worker(gpu):
    mode = 'flat' if gpu % 2 == 0 else 'deck'
    for seed in (gpu//2, gpu//2+2):
        out = f'artifacts/p2-15-{mode}-seed{seed}'
        train = [sys.executable, 'scripts/run_job.py', '--gpu', str(gpu), '--timeout', '1800',
                 'train', '--config', f'configs/p2-15-{mode}.json', '--seed', str(seed), '--out', out]
        result = subprocess.run(train, cwd=ROOT)
        if result.returncode:
            return {'gpu': gpu, 'failed': out, 'exit_code': result.returncode}
        other = 'deck' if mode == 'flat' else 'flat'
        cross = [sys.executable, 'scripts/run_job.py', '--gpu', str(gpu), '--timeout', '240',
                 'evaluate', '--config', out+'/config.json', '--checkpoint', out+'/checkpoint-001600.pt',
                 '--out', out+'__cross-'+other, '--episodes', '64', '--diagnostics', '--video',
                 '--video-envs', '64', '--video-camera-side', '4', '--support-mode', other,
                 '--support-preserve-goals', '--support-matched-material', '--support-calibration',
                 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
                 '--research-tag', 'phase:P2', '--research-tag', 'step:p2-15-terrain-training',
                 '--research-tag', 'purpose:cross-terrain', '--research-tag', 'terrain:'+other]
        result = subprocess.run(cross, cwd=ROOT)
        if result.returncode:
            return {'gpu': gpu, 'failed': out+'__cross-'+other, 'exit_code': result.returncode}
    return {'gpu': gpu, 'exit_code': 0}


if __name__ == '__main__':
    for mode in ('flat', 'deck'):
        for seed in range(4):
            p = ROOT/'artifacts'/f'p2-15-{mode}-seed{seed}'
            if p.exists() or p.with_suffix('.log').exists():
                raise RuntimeError(f'Existing attempt {p}; inspect active jobs before any restart')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
