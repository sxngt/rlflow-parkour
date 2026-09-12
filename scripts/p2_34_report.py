"""Completed-only P2-34 paired outcomes and unique training-step accounting."""
import json
from pathlib import Path
import sys

from audit_artifacts import audit
from audit_chained_evaluation import check as audit_chain
from p2_34_evaluate import evaluation_plan

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.evaluation_summary import load_report


def read(directory, name):
    return json.loads((directory / name).read_text())


def build_report():
    plan = evaluation_plan()
    budget = []
    for name in sorted({item['source'] for item in plan}):
        path = ROOT / name
        audit(path)
        run = read(path, 'run.json')
        metrics = list(map(json.loads, (path / 'metrics.jsonl').read_text().splitlines()))
        assert len(metrics) == 800 and metrics[0]['iteration'] == 1 and metrics[-1]['iteration'] == 800
        steps = run['config']['num_envs'] * run['config']['runner']['num_steps_per_env']
        assert steps == 24576
        assert all(m['total_environment_steps'] == (i + 1) * steps for i, m in enumerate(metrics))
        row = {'run': name, 'new_environment_steps': metrics[-1]['total_environment_steps'],
               'worker_wall_seconds': read(path.parent, path.name + '.supervisor.json')['wall_seconds'],
               'parent_checkpoint': run['lineage']['parent_checkpoint']}
        if run['config'].get('chain_training'):
            assert all(len(m['hop_environment_steps']) == 2 and sum(m['hop_environment_steps']) == steps for m in metrics)
            row['hop_environment_steps'] = [sum(m['hop_environment_steps'][i] for m in metrics) for i in range(2)]
            row['sampled_training_hop_successes'] = [sum(m['hop_successes'][i] for m in metrics) for i in range(2)]
        budget.append(row)
    assert sum(row['new_environment_steps'] for row in budget) == 157286400
    evaluations = {}
    for item in plan:
        path = ROOT / item['evaluation']
        audit(path)
        run = read(path, 'run.json')
        assert Path(run['checkpoint']['path']).resolve() == (ROOT / item['source'] / 'checkpoint-000800.pt').resolve()
        if run.get('chain_contract'):
            audit_chain(path)
        evaluations[(item['seed'], item['condition'], item['suite'])] = {
            'evaluation': item['evaluation'], 'reused_native_evaluation': item['reused'],
            'report': load_report(path), 'scenarios': read(path, 'scenarios.json')['episodes']}
    comparisons = []
    for seed in range(4):
        for suite in ('chain', 'deck-single', 'regression', 'split15'):
            a, b = [evaluations[(seed, condition, suite)] for condition in ('single', 'chain')]
            assert a['scenarios'] == b['scenarios']
            ar, br = a['report'], b['report']
            assert ar['episodes'] == br['episodes'] == 64
            pairs = list(zip(ar['results'], br['results']))
            assert all(x['scenario_id'] == y['scenario_id'] for x, y in pairs)
            comparisons.append({'seed': seed, 'suite': suite, 'episodes': 64,
                'single_training_successes': ar['successes'], 'chain_training_successes': br['successes'],
                'single_only_successes': sum(x['success'] and not y['success'] for x, y in pairs),
                'chain_only_successes': sum(y['success'] and not x['success'] for x, y in pairs),
                'single_by_distance': ar.get('by_distance'), 'chain_by_distance': br.get('by_distance'),
                'evaluations': [a['evaluation'], b['evaluation']]})
    return {'new_training_environment_steps': 157286400, 'training_runs': budget, 'comparisons': comparisons,
            'inference_scope': 'paired development scenarios; training seeds are independent units, not parallel environments',
            'budget_scope': 'eight new main training runs only; pilot steps and reused parent evaluations excluded and reported separately'}


if __name__ == '__main__':
    result = build_report()
    (ROOT / 'docs/p2-34-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    text = ['# P2-34 단일/연속 도약 학습 대조', '',
            '신규 본학습 환경 step: 157,286,400. 파일럿과 부모 평가 예산은 별도다.', '',
            '| seed | 평가군 | 단일 학습 성공/64 | 연속 학습 성공/64 |', '|---|---|---:|---:|']
    for row in result['comparisons']:
        text.append(f"| {row['seed']} | {row['suite']} | {row['single_training_successes']} | {row['chain_training_successes']} |")
    text += ['', '동일 개발 시나리오의 짝 비교다. 병렬 환경을 독립 학습 seed로 간주하지 않는다.',
             '연속 도약의 기존 비행/접촉 필드는 최종 시도 도약의 진단이며 전체 코스 성공과 구분한다.']
    (ROOT / 'docs/p2-34-comparison.md').write_text('\n'.join(text) + '\n')
    print('Validated 8 training budgets and 16 paired evaluation comparisons.')
