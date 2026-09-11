"""Eight bounded fixed-condition intermediate checkpoint evaluations."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]


def worker(seed):
    train = f'artifacts/p2-16-deck-seed{seed}'
    for update in (800, 1200):
        out = train + f'__checkpoint-{update:06d}-evaluation'
        command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '240',
                   'evaluate', '--config', train+'/config.json', '--checkpoint', train+f'/checkpoint-{update:06d}.pt',
                   '--out', out, '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64',
                   '--video-camera-side', '4', '--research-tag', 'purpose:checkpoint-diagnosis',
                   '--research-tag', f'checkpoint:{update}']
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return {'run': out, 'exit_code': result.returncode}
    return {'seed': seed, 'exit_code': 0}


if __name__ == '__main__':
    for seed in range(4):
        for update in (800, 1200):
            path = ROOT/'artifacts'/f'p2-16-deck-seed{seed}__checkpoint-{update:06d}-evaluation'
            if path.exists() or path.with_suffix('.log').exists():
                raise RuntimeError(f'Existing attempt {path}; inspect first')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(row['exit_code'] for row in results)))
