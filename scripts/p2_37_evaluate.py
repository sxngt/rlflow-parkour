"""Frozen checkpoint deck evaluation matched to existing continuous regression."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit

ROOT = Path(__file__).resolve().parents[1]


def evaluation_plan():
    return [dict(seed=seed, condition=condition,
                 source=f'artifacts/{prefix}-seed{seed}',
                 reference=f'artifacts/{prefix}-seed{seed}-regression',
                 evaluation=f'artifacts/p2-37-{condition}-seed{seed}-deck-regression-retry1')
            for seed in range(4) for condition, prefix in
            [('chain', 'p2-34-chain'), ('mixed', 'p2-36-mixed')]]


def worker(seed, plan):
    for item in plan:
        if item['seed'] != seed:
            continue
        source = item['source']
        command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '300',
            'evaluate', '--config', source + '/config.json', '--checkpoint', source + '/checkpoint-000800.pt',
            '--out', item['evaluation'], '--chain-hops', '1', '--support-mode', 'deck', '--support-matched-material',
            '--support-calibration', 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
            '--episodes', '64', '--evaluation-forward-m', '0', '.05', '.1', '.15',
            '--diagnostics', '--video', '--video-envs', '64', '--video-camera-side', '4',
            '--research-tag', 'phase:P2', '--research-tag', 'step:p2-37-support-transfer',
            '--research-tag', 'condition:' + item['condition'], '--research-tag', 'purpose:deck-regression']
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return dict(seed=seed, exit_code=result.returncode, evaluation=item['evaluation'])
        audit(ROOT / item['evaluation'])
    return dict(seed=seed, exit_code=0)


if __name__ == '__main__':
    plan = evaluation_plan()
    for item in plan:
        audit(ROOT / item['source'])
        audit(ROOT / item['reference'])
        path = ROOT / item['evaluation']
        if path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    (ROOT / 'artifacts/p2-37-evaluation-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda seed: worker(seed, plan), range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
