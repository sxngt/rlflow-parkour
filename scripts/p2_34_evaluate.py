"""Evaluate P2-34 paired conditions, reusing eight native final evaluations."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json'


def evaluation_plan():
    plan = []
    for seed in range(4):
        for condition in ('single', 'chain'):
            source = f'artifacts/p2-34-{condition}-seed{seed}'
            for suite, mode, hops in [('chain', 'deck', 2), ('deck-single', 'deck', 1),
                                      ('regression', 'continuous', 1), ('split15', 'split', 1)]:
                reused = (condition == 'single' and suite == 'deck-single') or (condition == 'chain' and suite == 'chain')
                out = source + ('__final-evaluation' if reused else '-' + suite)
                command = None
                if not reused:
                    command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '300',
                        'evaluate', '--config', source + '/config.json',
                        '--checkpoint', source + '/checkpoint-000800.pt', '--out', out,
                        '--support-mode', mode, '--support-matched-material', '--support-calibration', REFERENCE,
                        '--chain-hops', str(hops), '--episodes', '64', '--diagnostics',
                        '--video', '--video-envs', '64', '--video-camera-side', '4',
                        '--research-tag', 'phase:P2', '--research-tag', 'step:p2-34-chain-training',
                        '--research-tag', f'condition:{condition}', '--research-tag', f'purpose:{suite}']
                    if suite == 'regression':
                        command += ['--evaluation-forward-m', '0', '.05', '.1', '.15']
                plan.append({'seed': seed, 'condition': condition, 'suite': suite,
                             'source': source, 'evaluation': out, 'reused': reused, 'command': command})
    return plan


def worker(seed, plan):
    for item in plan:
        if item['seed'] != seed or item['reused']:
            continue
        result = subprocess.run(item['command'], cwd=ROOT)
        if result.returncode:
            return {'seed': seed, 'exit_code': result.returncode, 'evaluation': item['evaluation']}
        audit(ROOT / item['evaluation'])
    return {'seed': seed, 'exit_code': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    plan = evaluation_plan()
    assert len(plan) == 32 and sum(p['reused'] for p in plan) == 8
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        sys.exit(0)
    for source in sorted({p['source'] for p in plan}):
        audit(ROOT / source)
    for item in plan:
        path = ROOT / item['evaluation']
        if item['reused']:
            audit(path)
        elif path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing evaluation attempt: {path}')
    (ROOT / 'artifacts/p2-34-evaluation-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda seed: worker(seed, plan), range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
