"""Fixed-endpoint retention comparison, only after every run and archive completes."""
import copy
import json
from pathlib import Path
import sys

from audit_artifacts import audit
from audit_chained_evaluation import check as audit_chain
from audit_retention_training import check as audit_retention
from p2_34_archive_audit import digest
from p2_36_evaluate import evaluation_plan

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.evaluation_summary import load_report


def read(path, name):
    return json.loads((path / name).read_text())


def evaluation(path, checkpoint, mixed):
    audit_chain(path)
    run, scenarios = read(path, 'run.json'), read(path, 'scenarios.json')['episodes']
    assert Path(run['checkpoint']['path']).resolve() == checkpoint.resolve()
    assert run['checkpoint']['completed_iterations'] == 800
    assert run['action_evaluation']['mode'] == 'mean'
    report = load_report(path)
    assert report['episodes'] == len(scenarios) == 64
    manifests = list((ROOT / 'result').glob(f'*__{path.name}/manifest.json'))
    assert len(manifests) == 1
    manifest = manifests[0]
    archive = json.loads(manifest.read_text())
    assert archive['evaluation_run'] == path.name and archive['checkpoint'] == run['checkpoint']
    assert digest(manifest.parent / archive['video']) == archive['source_video_sha256']
    event = archive['chain_events']
    assert digest(path / 'chain-events.json') == digest(manifest.parent / event['file']) == event['sha256']
    replay = read(path, 'replay.json')
    assert len(replay['visible_env_ids']) == len(archive['video_episodes']) == 64
    assert replay['camera']['framing_side'] == 4
    if mixed:
        assert {'phase:P2', 'step:p2-36-single-task-retention'} <= set(archive['research_tags'])
        assert '50%' in archive['title']
    events = read(path, 'chain-events.json')
    return dict(report=report, scenarios=scenarios, manifest=str(manifest.relative_to(ROOT)),
                first_hop_successes=sum(h['segment'] == 0 and h['metrics']['success'] for h in events['hops']))


def build_report():
    budget, comparisons = [], []
    for seed in range(4):
        mixed = ROOT / f'artifacts/p2-36-mixed-seed{seed}'
        control = ROOT / f'artifacts/p2-34-chain-seed{seed}'
        accounting = audit_retention(mixed)
        audit(control)
        a, b = read(control, 'run.json'), read(mixed, 'run.json')
        assert a['lineage']['parent_checkpoint'] == b['lineage']['parent_checkpoint']
        ac, bc = copy.deepcopy(a['config']), copy.deepcopy(b['config'])
        bc.pop('retention_training')
        for cfg in (ac, bc):
            cfg.pop('research_tags', None)
        assert ac == bc, 'Paired conditions differ beyond declared mixture and tags'
        assert accounting['first_update'] == 1 and accounting['last_update'] == accounting['updates'] == 800
        expected = 19660800
        for path in (control, mixed):
            rows = [json.loads(line) for line in (path / 'metrics.jsonl').read_text().splitlines()]
            assert len(rows) == 800
            assert all(r['iteration'] == i + 1 and r['total_environment_steps'] == (i + 1) * 24576
                       for i, r in enumerate(rows))
        budget.append(dict(seed=seed, new_environment_steps=expected, reused_control_steps=expected,
            mixed_accounting=accounting,
            mixed_worker_seconds=read(mixed.parent, mixed.name + '.supervisor.json')['wall_seconds'],
            control_worker_seconds=read(control.parent, control.name + '.supervisor.json')['wall_seconds']))
    for item in evaluation_plan():
        seed = item['seed']
        a = evaluation(ROOT / item['control_evaluation'],
                       ROOT / f'artifacts/p2-34-chain-seed{seed}/checkpoint-000800.pt', False)
        b = evaluation(ROOT / item['evaluation'], ROOT / item['source'] / 'checkpoint-000800.pt', True)
        assert a['scenarios'] == b['scenarios']
        pairs = list(zip(a['report']['results'], b['report']['results']))
        assert all(x['scenario_id'] == y['scenario_id'] for x, y in pairs)
        comparisons.append(dict(seed=seed, suite=item['suite'], episodes=64,
            control_successes=a['report']['successes'], mixed_successes=b['report']['successes'],
            control_only_successes=sum(x['success'] and not y['success'] for x, y in pairs),
            mixed_only_successes=sum(y['success'] and not x['success'] for x, y in pairs),
            control_first_hop_successes=a['first_hop_successes'], mixed_first_hop_successes=b['first_hop_successes'],
            control_by_distance=a['report'].get('by_distance'), mixed_by_distance=b['report'].get('by_distance'),
            evaluations=[item['control_evaluation'], item['evaluation']], manifests=[a['manifest'], b['manifest']]))
    assert sum(r['new_environment_steps'] for r in budget) == 78643200
    return dict(new_training_environment_steps=78643200, reused_control_environment_steps=78643200,
                pilot_steps_excluded=1496064, training_runs=budget, comparisons=comparisons,
                scope='fixed 800-update paired development evaluation; four training seeds, not 64 independent policies')


if __name__ == '__main__':
    result = build_report()
    lines = ['# P2-36 단일 과제 혼합의 고정 예산 비교', '',
             '신규 혼합 학습 78,643,200 step. 대조군 P2-34의 같은 예산 결과를 재사용했다.', '',
             '| seed | 평가군 | 연속 전용 /64 | 단일 과제 혼합 /64 |', '|---|---|---|---|']
    for r in result['comparisons']:
        lines.append(f"| {r['seed']} | {r['suite']} | {r['control_successes']} | {r['mixed_successes']} |")
    lines += ['', '동일 seed/시나리오의 개발군 비교이며, 최종 모델 승격이나 최종 시험 성공을 의미하지 않는다.']
    (ROOT / 'docs/p2-36-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/p2-36-comparison.md').write_text('\n'.join(lines) + '\n')
    print('Validated four paired training budgets and 32 evaluated/archived results.')
