"""Four bounded fresh bounded-exploration runs, each followed by final evaluation."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def worker(seed):
    out = f'artifacts/p2-25-deck-seed{seed}'
    command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '1800',
               'train', '--config', 'configs/p2-25-deck.json', '--seed', str(seed), '--out', out]
    result = subprocess.run(command, cwd=ROOT)
    return {'run': out, 'exit_code': result.returncode}


if __name__ == '__main__':
    for seed in range(4):
        path = ROOT / 'artifacts' / f'p2-25-deck-seed{seed}'
        if path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt {path}; inspect before restarting')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(row['exit_code'] for row in results)))
