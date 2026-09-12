"""Evaluate completed P2-38 pilots; never use pilot checkpoints as main parents."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_retention_training import check
from audit_chained_evaluation import check as audit_evaluation

ROOT = Path(__file__).resolve().parents[1]


def worker(item):
    mode, suite, gpu = item
    source = f'artifacts/p2-38-{mode}-profile-seed2'
    out = f'artifacts/p2-38-{mode}-pilot-{suite}'
    command = [sys.executable, 'scripts/run_job.py', '--gpu', str(gpu), '--timeout', '300',
        'evaluate', '--config', source + '/config.json', '--checkpoint', source + '/checkpoint-000060.pt',
        '--out', out, '--chain-hops', '2' if suite == 'chain' else '1',
        '--support-mode', 'deck' if suite == 'chain' else 'continuous', '--support-matched-material',
        '--support-calibration', 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
        '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64', '--video-camera-side', '4',
        '--research-tag', 'phase:P2', '--research-tag', 'step:p2-38-support-mixture',
        '--research-tag', 'condition:' + mode, '--research-tag', 'purpose:pilot-' + suite]
    if suite == 'regression':
        command += ['--evaluation-forward-m', '0', '.05', '.1', '.15']
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode == 0:
        audit_evaluation(ROOT / out)
    return dict(mode=mode, suite=suite, exit_code=result.returncode)


if __name__ == '__main__':
    plan = [(mode, suite, gpu) for gpu, (mode, suite) in enumerate(
        [('deck', 'chain'), ('deck', 'regression'), ('continuous', 'chain'), ('continuous', 'regression')])]
    for mode in ('deck', 'continuous'):
        result = check(ROOT / f'artifacts/p2-38-{mode}-profile-seed2')
        assert result['updates'] == 60 and result['new_steps'] == 1474560
    for mode, suite, _ in plan:
        path = ROOT / f'artifacts/p2-38-{mode}-pilot-{suite}'
        if path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, plan))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
