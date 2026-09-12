"""Fixed intermediate checkpoint evaluations; no new training or best-model selection."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys

from audit_artifacts import audit
from p2_34_evaluate import evaluation_plan as previous_plan

ROOT = Path(__file__).resolve().parents[1]


def evaluation_plan():
    reference = 'artifacts/p2-11-curriculum-seed0__final-evaluation/run.json'
    plan = []
    for seed in range(4):
        source = f'artifacts/p2-34-chain-seed{seed}'
        for update in (200, 400, 600):
            for suite, mode, hops in [('chain', 'deck', 2), ('regression', 'continuous', 1)]:
                checkpoint = source + f'/checkpoint-{update:06d}.pt'
                out = f'artifacts/p2-35-chain-seed{seed}-update{update:04d}-{suite}'
                command = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '300',
                    'evaluate', '--config', source + '/config.json', '--checkpoint', checkpoint,
                    '--out', out, '--support-mode', mode, '--support-matched-material',
                    '--support-calibration', reference, '--chain-hops', str(hops),
                    '--episodes', '64', '--diagnostics', '--video', '--video-envs', '64',
                    '--video-camera-side', '4', '--research-tag', 'phase:P2',
                    '--research-tag', 'step:p2-35-chain-retention-timeline',
                    '--research-tag', f'checkpoint-update:{update}', '--research-tag', f'purpose:{suite}']
                if suite == 'regression':
                    command += ['--evaluation-forward-m', '0', '.05', '.1', '.15']
                plan.append(dict(seed=seed, update=update, suite=suite, source=source,
                                 checkpoint=checkpoint, evaluation=out, command=command))
    return plan


def worker(seed, plan):
    for item in plan:
        if item['seed'] != seed:
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
    assert len(plan) == 24 and len({x['evaluation'] for x in plan}) == 24
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        sys.exit(0)
    for source in sorted({x['source'] for x in plan}):
        audit(ROOT / source)
    for item in previous_plan():
        if item['condition'] == 'chain' and item['suite'] in ('chain', 'regression'):
            audit(ROOT / item['evaluation'])
    for item in plan:
        assert (ROOT / item['checkpoint']).is_file(), item['checkpoint']
        path = ROOT / item['evaluation']
        if path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    (ROOT / 'artifacts/p2-35-evaluation-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda seed: worker(seed, plan), range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
