"""Bounded four-seed, three-terrain evaluation from the P2-14 protocol."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def commands(seed, modes=('flat', 'continuous', 'split')):
    training = f'artifacts/p2-11-curriculum-seed{seed}'
    for mode in modes:
        out = f'artifacts/p2-14-{mode}-seed{seed}'
        yield [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '240',
               'evaluate', '--config', training+'/config.json',
               '--checkpoint', training+'/checkpoint-001600.pt', '--out', out,
               '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64',
               '--video-camera-side', '4', '--support-mode', mode,
               '--support-calibration', 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
               '--research-tag', 'phase:P2', '--research-tag', 'step:p2-14-support',
               '--research-tag', 'terrain:'+mode, '--research-tag', 'purpose:fixed-policy-transfer']


def run_seed(seed, modes):
    for command in commands(seed, modes):
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return {'seed': seed, 'exit_code': result.returncode, 'failed_command': command}
    return {'seed': seed, 'exit_code': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modes', nargs='+', choices=['flat', 'continuous', 'split', 'deck'],
                        default=['flat', 'continuous', 'split'])
    args = parser.parse_args()
    if len(set(args.modes)) != len(args.modes):
        parser.error('Duplicate modes would create duplicate attempts')
    for seed in range(4):
        for command in commands(seed, args.modes):
            out = ROOT / command[command.index('--out')+1]
            if out.exists() or out.with_suffix('.log').exists():
                raise RuntimeError(f'Existing attempt: {out}; inspect it instead of restarting the batch')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda seed: run_seed(seed, args.modes), range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
