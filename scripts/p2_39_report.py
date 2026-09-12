"""Completed-only matched support-training comparison with placement accounting."""
from collections import Counter
import copy
import json
from pathlib import Path
import sys

from audit_retention_training import check
from p2_36_report import evaluation, read
from p2_39_evaluate import evaluation_plan

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.support_assignment import support_assignment


def training(path):
    accounting = check(path)
    run = read(path, 'run.json')
    assert accounting['updates'] == accounting['last_update'] == 800
    assert accounting['first_update'] == 1 and accounting['new_steps'] == 19660800
    rows = [json.loads(line) for line in (path / 'metrics.jsonl').read_text().splitlines()]
    assert all(r['total_environment_steps'] == (i + 1) * 24576 for i, r in enumerate(rows))
    plan = read(path, 'support-assignment.json')
    assert plan == support_assignment(run['config'])
    inspected = read(path, 'support-inspection.json')
    actual = Counter((r['env_index'], r['mode']) for r in inspected['colliders'])
    expected = Counter({(i, g['mode']): len(g['layout']['surfaces']) for g in plan['groups']
                        for i in range(g['env_start'], g['env_stop'])})
    assert actual == expected and inspected['inspected_environments'] == 1024
    supervisor = read(path.parent, path.name + '.supervisor.json')
    return dict(run=str(path.relative_to(ROOT)), accounting=accounting,
                worker_seconds=supervisor['wall_seconds'],
                update_seconds=sum(r['wall_seconds'] for r in rows),
                inspected_support_colliders=sum(actual.values()), parent=run['lineage']['parent_checkpoint'])


def build_report():
    budgets = []
    for seed in range(4):
        paths = [ROOT / f'artifacts/p2-38-continuous-seed{seed}', ROOT / f'artifacts/p2-39-coverage-seed{seed}']
        pair = [training(p) for p in paths]
        assert pair[0]['parent'] == pair[1]['parent']
        configs = [copy.deepcopy(read(p, 'config.json')) for p in paths]
        for cfg, goals in zip(configs, ([0., .15], [0., .05, .1, .15])):
            cfg.pop('research_tags', None)
            assert cfg['retention_training'].pop('single_goal_choices_m') == goals
        assert configs[0] == configs[1], 'Unexpected paired training configuration difference'
        budgets.extend(pair)
    plan = evaluation_plan()
    evaluations = {}
    for item in plan:
        value = evaluation(ROOT / item['evaluation'], ROOT / item['source'] / 'checkpoint-000800.pt', False)
        archive = json.loads((ROOT / value['manifest']).read_text())
        step = 'step:p2-38-support-mixture' if item['condition'] == 'endpoint' else 'step:p2-39-goal-coverage'
        assert {'phase:P2', step} <= set(archive['research_tags'])
        assert '단일 continuous' in archive['title']
        if item['condition'] == 'coverage':
            assert '0·5·10·15cm' in archive['title']
        evaluations[(item['seed'], item['condition'], item['suite'])] = value
    comparisons = []
    for seed in range(4):
        for suite in ('chain', 'deck-regression', 'regression', 'split15'):
            a, b = [evaluations[(seed, mode, suite)] for mode in ('endpoint', 'coverage')]
            assert a['scenarios'] == b['scenarios']
            pairs = list(zip(a['report']['results'], b['report']['results']))
            assert len(pairs) == 64 and all(x['scenario_id'] == y['scenario_id'] for x, y in pairs)
            comparisons.append(dict(seed=seed, suite=suite, episodes=64,
                endpoint_training_successes=a['report']['successes'], coverage_training_successes=b['report']['successes'],
                endpoint_only_successes=sum(x['success'] and not y['success'] for x, y in pairs),
                coverage_only_successes=sum(y['success'] and not x['success'] for x, y in pairs),
                endpoint_training_first_hop_successes=a['first_hop_successes'],
                coverage_training_first_hop_successes=b['first_hop_successes'],
                endpoint_training_by_distance=a['report'].get('by_distance'),
                coverage_training_by_distance=b['report'].get('by_distance'),
                manifests=[a['manifest'], b['manifest']]))
    total = sum(r['accounting']['new_steps'] for r in budgets)
    assert total == 157286400
    new_steps = sum(r['accounting']['new_steps'] for r in budgets if 'p2-39-' in r['run'])
    reused_steps = total - new_steps
    assert new_steps == reused_steps == 78643200
    return dict(new_main_training_steps=new_steps, reused_control_steps=reused_steps,
                training_runs=budgets, comparisons=comparisons,
                scope='four paired seeds, fixed final checkpoint, development evaluation; P2-38 endpoint controls reused explicitly; pilots excluded')


if __name__ == '__main__':
    result = build_report()
    text = ['# P2-39 단일 과제의 목표 거리 범위 비교', '',
            'P2-38 두 거리 대조78,643,200step을 재사용하고 네 거리 조건78,643,200step을 새로 학습했다.', '',
            '| seed | 평가군 | 0·15cm 학습 /64 | 0·5·10·15cm 학습 /64 |', '|---|---|---|---|']
    for row in result['comparisons']:
        text.append(f"| {row['seed']} | {row['suite']} | {row['endpoint_training_successes']} | {row['coverage_training_successes']} |")
    (ROOT / 'docs/p2-39-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/p2-39-comparison.md').write_text('\n'.join(text) + '\n')
    print('Verified eight training budgets/placements and 32 evaluation archives.')
