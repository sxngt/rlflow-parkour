"""Completed-only fixed checkpoint timeline with paired scenarios and archive checks."""
import json
from pathlib import Path
import sys

from audit_chained_evaluation import check
from p2_34_archive_audit import digest
from p2_34_evaluate import evaluation_plan as previous_plan
from p2_35_evaluate import evaluation_plan

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.evaluation_summary import load_report


def build_report():
    plan = evaluation_plan()
    for item in previous_plan():
        if item['condition'] == 'chain' and item['suite'] in ('chain', 'regression'):
            plan.append(dict(item, update=800, reused=True,
                             checkpoint=item['source'] + '/checkpoint-000800.pt'))
    assert len(plan) == 32
    scenarios, rows = {}, []
    for item in sorted(plan, key=lambda x: (x['seed'], x['update'], x['suite'])):
        directory = ROOT / item['evaluation']
        check(directory)
        read = lambda name: json.loads((directory / name).read_text())
        run, episodes = read('run.json'), read('scenarios.json')['episodes']
        key = item['seed'], item['suite']
        assert scenarios.setdefault(key, episodes) == episodes
        assert Path(run['checkpoint']['path']).resolve() == (ROOT / item['checkpoint']).resolve()
        assert run['checkpoint']['completed_iterations'] == item['update']
        assert run['action_evaluation']['mode'] == 'mean'
        manifests = list((ROOT / 'result').glob(f'*__{directory.name}/manifest.json'))
        assert len(manifests) == 1
        manifest = manifests[0]
        archive = json.loads(manifest.read_text())
        assert archive['evaluation_run'] == directory.name
        assert archive['checkpoint'] == run['checkpoint']
        assert digest(manifest.parent / archive['video']) == archive['source_video_sha256']
        event = archive['chain_events']
        assert digest(directory / 'chain-events.json') == event['sha256']
        assert digest(manifest.parent / event['file']) == event['sha256']
        replay = read('replay.json')
        assert len(replay['visible_env_ids']) == len(archive['video_episodes']) == 64
        assert replay['camera']['framing_side'] == 4
        if not item.get('reused'):
            assert {'phase:P2', 'step:p2-35-chain-retention-timeline',
                    f"checkpoint-update:{item['update']}"} <= set(archive['research_tags'])
        report = load_report(directory)
        assert report['episodes'] == 64
        events = read('chain-events.json')
        supervisor = json.loads(directory.with_suffix('.supervisor.json').read_text())
        rows.append(dict(seed=item['seed'], update=item['update'], suite=item['suite'],
            evaluation=item['evaluation'], reused=item.get('reused', False),
            successes=report['successes'], episodes=64, by_distance=report.get('by_distance'),
            first_hop_successes=sum(e['segment'] == 0 and e['metrics']['success'] for e in events['hops']),
            terminal_gate_false_counts={k: sum(not r[k] for r in report['results']) for k in
                ('valid_flight', 'launch_in_region', 'travel_requirement_met',
                 'first_touch_all_within', 'final_all_feet_in_radius', 'stabilized_once')},
            worker_wall_seconds=supervisor['wall_seconds'], manifest=str(manifest.relative_to(ROOT))))
    return dict(new_training_steps=0, new_evaluation_episodes=1536,
                reused_evaluation_episodes=512,
                new_evaluation_worker_seconds=sum(r['worker_wall_seconds'] for r in rows if not r['reused']),
                scope='fixed development timeline; no replacement of P2-34 final endpoint; seeds are independent units',
                results=rows)


if __name__ == '__main__':
    result = build_report()
    text = ['# P2-35 고정 checkpoint 시간 경과 평가', '',
            '신규 학습 0 step. 신규 평가 1,536 episode, P2-34 최종 평가 512 episode 재사용.', '',
            '| seed | update | 첫 도약 /64 | 두 도약 완주 /64 | continuous 0/5/10/15cm 각16 |',
            '|---|---|---|---|---|']
    for seed in range(4):
        for update in (200, 400, 600, 800):
            pair = {r['suite']: r for r in result['results'] if r['seed'] == seed and r['update'] == update}
            chain = pair['chain']
            distances = pair['regression']['by_distance']
            counts = '/'.join(str(distances[str(d)]['successes']) for d in (0.0, .05, .1, .15))
            text.append(f"| {seed} | {update} | {chain['first_hop_successes']} | {chain['successes']} | {counts} |")
    text += ['', '800 update는 기존 결과 재사용이다. 개발군의 탐색적 분석이며 좋은 시점만 골라 기존 결과를 대체하지 않는다.']
    (ROOT / 'docs/p2-35-timeline.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/p2-35-timeline.md').write_text('\n'.join(text) + '\n')
    print('Validated all 32 timeline evaluations, paired scenarios, and result archives.')
