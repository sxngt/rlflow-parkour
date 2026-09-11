"""Bounded four-seed, three-terrain evaluation from the P2-14 protocol."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def commands(seed):
    training = f'artifacts/p2-11-curriculum-seed{seed}'
    for mode in ('flat', 'continuous', 'split'):
        out = f'artifacts/p2-14-{mode}-seed{seed}'
        yield [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '240',
               'evaluate', '--config', training+'/config.json',
               '--checkpoint', training+'/checkpoint-001600.pt', '--out', out,
               '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64',
               '--video-camera-side', '4', '--support-mode', mode,
               '--support-calibration', 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
               '--research-tag', 'phase:P2', '--research-tag', 'step:p2-14-support',
               '--research-tag', 'terrain:'+mode, '--research-tag', 'purpose:fixed-policy-transfer']


def run_seed(seed):
    for command in commands(seed):
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return {'seed': seed, 'exit_code': result.returncode, 'failed_command': command}
    return {'seed': seed, 'exit_code': 0}


if __name__ == '__main__':
    for seed in range(4):
        for command in commands(seed):
            out = ROOT / command[command.index('--out')+1]
            if out.exists() or out.with_suffix('.log').exists():
                raise RuntimeError(f'Existing attempt: {out}; inspect it instead of restarting the batch')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_seed, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
