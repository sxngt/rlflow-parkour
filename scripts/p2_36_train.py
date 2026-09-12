"""Four fixed-budget retention forks after completed implementation gates."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit
from audit_chained_evaluation import check as audit_chain
from audit_retention_training import check as audit_retention

ROOT = Path(__file__).resolve().parents[1]


def worker(seed):
    command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '1800',
               'train', '--config', 'configs/p2-36-mixed.json', '--seed', str(seed),
               '--fork-from', f'artifacts/p2-31-mixed-seed{seed}/checkpoint-000800.pt',
               '--out', f'artifacts/p2-36-mixed-seed{seed}']
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode == 0:
        audit_retention(ROOT / f'artifacts/p2-36-mixed-seed{seed}')
        audit_chain(ROOT / f'artifacts/p2-36-mixed-seed{seed}__final-evaluation')
    return dict(seed=seed, exit_code=result.returncode)


if __name__ == '__main__':
    config = json.loads((ROOT / 'configs/p2-36-mixed.json').read_text())
    assert config['iterations'] == 800 and config['num_envs'] == 1024
    assert config['runner']['num_steps_per_env'] == 24
    for name in ('p2-36-mixed-smoke', 'p2-36-mixed-smoke-resume', 'p2-36-mixed-profile-seed2'):
        audit_retention(ROOT / 'artifacts' / name)
    for name in ('p2-36-initial-seed2-regression', 'p2-36-profile-seed2-chain', 'p2-36-profile-seed2-regression'):
        audit_chain(ROOT / 'artifacts' / name)
    def results(name):
        return json.loads((ROOT / 'artifacts' / name / 'evaluation.json').read_text())['results']
    assert results('p2-36-initial-seed2-regression') == results('p2-34-initial-seed2-single-regression')
    for seed in range(4):
        audit(ROOT / f'artifacts/p2-31-mixed-seed{seed}')
        audit(ROOT / f'artifacts/p2-34-chain-seed{seed}')
        path = ROOT / f'artifacts/p2-36-mixed-seed{seed}'
        if path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
