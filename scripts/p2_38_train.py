"""Fixed eight-run support-mixture comparison after verified physical gates."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit
from audit_retention_training import check as audit_training
from audit_chained_evaluation import check as audit_evaluation

ROOT = Path(__file__).resolve().parents[1]


def worker(seed):
    for mode in (('deck', 'continuous') if seed % 2 == 0 else ('continuous', 'deck')):
        source = f'artifacts/p2-38-{mode}-seed{seed}'
        command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '2400',
                   'train', '--config', f'configs/p2-38-{mode}.json', '--seed', str(seed),
                   '--fork-from', f'artifacts/p2-31-mixed-seed{seed}/checkpoint-000800.pt', '--out', source]
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return dict(seed=seed, mode=mode, exit_code=result.returncode)
        checked = audit_training(ROOT / source)
        assert checked['updates'] == 800 and checked['new_steps'] == 19660800
        audit_evaluation(ROOT / (source + '__final-evaluation'))
    return dict(seed=seed, exit_code=0)


if __name__ == '__main__':
    for mode in ('deck', 'continuous'):
        config = json.loads((ROOT / f'configs/p2-38-{mode}.json').read_text())
        assert config['iterations'] == 800 and config['num_envs'] == 1024
        assert config['runner']['num_steps_per_env'] == 24
        for suffix in ('scene-smoke', 'training-smoke', 'training-resume', 'profile-seed2'):
            audit_training(ROOT / f'artifacts/p2-38-{mode}-{suffix}')
        audit(ROOT / f'artifacts/p2-38-{mode}-physical-probe')
        probe = json.loads((ROOT / f'artifacts/p2-38-{mode}-physical-probe/probe.json').read_text())
        assert probe['own_support_passed'] and probe['isolation_passed']
        for suite in ('chain', 'regression'):
            audit_evaluation(ROOT / f'artifacts/p2-38-{mode}-pilot-{suite}')
    references = []
    for mode in ('independent', 'replicated'):
        path = ROOT / f'artifacts/p2-38-deck-{mode}-initial-evaluation'
        audit_evaluation(path)
        references.append(json.loads((path / 'evaluation.json').read_text())['results'])
    assert references[0] == references[1]
    for seed in range(4):
        audit(ROOT / f'artifacts/p2-31-mixed-seed{seed}')
        for mode in ('deck', 'continuous'):
            path = ROOT / f'artifacts/p2-38-{mode}-seed{seed}'
            if path.exists() or path.with_suffix('.log').exists():
                raise RuntimeError(f'Existing attempt: {path}')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
