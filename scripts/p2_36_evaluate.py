"""Evaluate all four retention models and reference the fixed P2-34 controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit
from audit_retention_training import check as audit_retention
from p2_34_evaluate import evaluation_plan as control_plan

ROOT = Path(__file__).resolve().parents[1]


def evaluation_plan():
    plan = []
    for control in control_plan():
        if control['condition'] != 'chain':
            continue
        seed, suite = control['seed'], control['suite']
        source = f'artifacts/p2-36-mixed-seed{seed}'
        native = suite == 'chain'
        out = source + ('__final-evaluation' if native else '-' + suite)
        command = None
        if not native:
            mode = {'deck-single': 'deck', 'regression': 'continuous', 'split15': 'split'}[suite]
            command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '300',
                'evaluate', '--config', source + '/config.json', '--checkpoint', source + '/checkpoint-000800.pt',
                '--out', out, '--chain-hops', '1', '--support-mode', mode, '--support-matched-material',
                '--support-calibration', 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
                '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64', '--video-camera-side', '4',
                '--research-tag', 'phase:P2', '--research-tag', 'step:p2-36-single-task-retention',
                '--research-tag', 'condition:mixed', '--research-tag', f'purpose:{suite}']
            if suite == 'regression':
                command += ['--evaluation-forward-m', '0', '.05', '.1', '.15']
        plan.append(dict(seed=seed, suite=suite, source=source, evaluation=out,
                         reused_native=native, control_evaluation=control['evaluation'], command=command))
    return plan


def worker(seed, plan):
    for item in plan:
        if item['seed'] != seed or item['reused_native']:
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
    assert len(plan) == 16 and sum(p['reused_native'] for p in plan) == 4
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        sys.exit(0)
    for source in sorted({p['source'] for p in plan}):
        result = audit_retention(ROOT / source)
        assert result['updates'] == result['last_update'] == 800
        assert result['new_steps'] == 19660800
    for item in plan:
        audit(ROOT / item['control_evaluation'])
        path = ROOT / item['evaluation']
        if item['reused_native']:
            audit(path)
        elif path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    (ROOT / 'artifacts/p2-36-evaluation-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda seed: worker(seed, plan), range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
