"""P2-34 paired single/chained PPO forks, fixed 800-update budgets per run."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit

ROOT = Path(__file__).resolve().parents[1]


def worker(seed):
    # Balance which condition runs first across the four GPUs.
    conditions = ('single', 'chain') if seed % 2 == 0 else ('chain', 'single')
    for condition in conditions:
        command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '1800',
                   'train', '--config', f'configs/p2-34-{condition}.json', '--seed', str(seed),
                   '--fork-from', f'artifacts/p2-31-mixed-seed{seed}/checkpoint-000800.pt',
                   '--out', f'artifacts/p2-34-{condition}-seed{seed}']
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return {'seed': seed, 'condition': condition, 'exit_code': result.returncode}
    return {'seed': seed, 'exit_code': 0}


if __name__ == '__main__':
    for name in ('p2-34-chain-smoke', 'p2-34-chain-smoke-resume', 'p2-34-chain-profile-seed2',
                 'p2-34-auto-evaluation-smoke'):
        audit(ROOT / 'artifacts' / name)
    for seed in range(4):
        audit(ROOT / 'artifacts' / f'p2-31-mixed-seed{seed}')
        for condition in ('single', 'chain'):
            p = ROOT / 'artifacts' / f'p2-34-{condition}-seed{seed}'
            if p.exists() or p.with_suffix('.log').exists():
                raise RuntimeError(f'Existing attempt: {p}')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
