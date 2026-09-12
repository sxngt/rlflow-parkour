"""Complete P2-39 evaluation matrix: four new native, 16 control and 12 additional results."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit
from audit_retention_training import check

ROOT = Path(__file__).resolve().parents[1]


def evaluation_plan():
    plan = []
    for seed in range(4):
        for condition in ('endpoint', 'coverage'):
            source = (f'artifacts/p2-38-continuous-seed{seed}' if condition == 'endpoint'
                      else f'artifacts/p2-39-coverage-seed{seed}')
            for suite, mode in [('chain', 'deck'), ('deck-regression', 'deck'),
                                ('regression', 'continuous'), ('split15', 'split')]:
                reused = condition == 'endpoint' or suite == 'chain'
                out = source + ('__final-evaluation' if suite == 'chain' else '-' + suite)
                command = None
                if not reused:
                    command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '300',
                        'evaluate', '--config', source + '/config.json', '--checkpoint', source + '/checkpoint-000800.pt',
                        '--out', out, '--chain-hops', '1', '--support-mode', mode, '--support-matched-material',
                        '--support-calibration', 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
                        '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64', '--video-camera-side', '4',
                        '--research-tag', 'phase:P2', '--research-tag', 'step:p2-39-goal-coverage',
                        '--research-tag', 'condition:' + condition, '--research-tag', 'purpose:' + suite]
                    if suite in ('deck-regression', 'regression'):
                        command += ['--evaluation-forward-m', '0', '.05', '.1', '.15']
                plan.append(dict(seed=seed, condition=condition, suite=suite, source=source,
                                 evaluation=out, reused_existing=reused, command=command))
    return plan


def worker(seed, plan):
    for item in plan:
        if item['seed'] != seed or item['reused_existing']:
            continue
        result = subprocess.run(item['command'], cwd=ROOT)
        if result.returncode:
            return dict(seed=seed, exit_code=result.returncode, evaluation=item['evaluation'])
        audit(ROOT / item['evaluation'])
    return dict(seed=seed, exit_code=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    plan = evaluation_plan()
    assert len(plan) == len({p['evaluation'] for p in plan}) == 32
    assert sum(p['reused_existing'] for p in plan) == 20
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        sys.exit(0)
    for source in sorted({p['source'] for p in plan}):
        record = check(ROOT / source)
        assert record['updates'] == record['last_update'] == 800 and record['first_update'] == 1
        assert record['new_steps'] == 19660800
    for item in plan:
        path = ROOT / item['evaluation']
        if item['reused_existing']:
            audit(path)
        elif path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    (ROOT / 'artifacts/p2-39-evaluation-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda seed: worker(seed, plan), range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
