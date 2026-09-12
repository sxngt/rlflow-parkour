"""Completed matched support comparisons with explicit contract and archive audits."""
import copy
import json
from pathlib import Path

from p2_36_report import evaluation, read
from p2_37_evaluate import evaluation_plan

ROOT = Path(__file__).resolve().parents[1]


def build_report():
    rows = []
    worker_seconds = 0.
    for item in evaluation_plan():
        deck, continuous = ROOT / item['evaluation'], ROOT / item['reference']
        checkpoint = ROOT / item['source'] / 'checkpoint-000800.pt'
        a, b = evaluation(deck, checkpoint, False), evaluation(continuous, checkpoint, False)
        assert a['scenarios'] == b['scenarios']
        ar, br = read(deck, 'run.json'), read(continuous, 'run.json')
        ac, bc = copy.deepcopy(ar['config']), copy.deepcopy(br['config'])
        ac.pop('research_tags', None); bc.pop('research_tags', None)
        assert ac == bc, 'Policy/environment configuration differs beyond research tags'
        for key in ('checkpoint', 'action_evaluation', 'nominal_foot_xy_m', 'chain_contract'):
            assert ar[key] == br[key], (item, key)
        sa, sb = copy.deepcopy(ar['evaluation_support']), copy.deepcopy(br['evaluation_support'])
        assert sa.pop('mode') == 'deck' and sb.pop('mode') == 'continuous'
        sa.pop('layout'); sb.pop('layout')
        assert sa == sb, 'Support calibration/material contract differs beyond geometry'
        manifest = json.loads((ROOT / a['manifest']).read_text())
        assert {'phase:P2', 'step:p2-37-support-transfer'} <= set(manifest['research_tags'])
        worker_seconds += read(deck.parent, deck.name + '.supervisor.json')['wall_seconds']
        for distance in (0., .05, .1, .15):
            pairs = [(x, y) for x, y in zip(a['report']['results'], b['report']['results'])
                     if abs(x['goal_forward_m'] - distance) < 1e-7]
            assert len(pairs) == 16
            assert all(x['scenario_id'] == y['scenario_id'] and x['goal_forward_m'] == y['goal_forward_m']
                       for x, y in pairs)
            gates = ('valid_flight', 'launch_in_region', 'travel_requirement_met',
                     'first_touch_all_within', 'final_all_feet_in_radius', 'stabilized_once')
            rows.append(dict(seed=item['seed'], condition=item['condition'], distance_m=distance, episodes=16,
                deck_successes=sum(x['success'] for x, y in pairs),
                continuous_successes=sum(y['success'] for x, y in pairs),
                deck_only_successes=sum(x['success'] and not y['success'] for x, y in pairs),
                continuous_only_successes=sum(y['success'] and not x['success'] for x, y in pairs),
                deck_gate_false_counts={k: sum(not x[k] for x, y in pairs) for k in gates},
                continuous_gate_false_counts={k: sum(not y[k] for x, y in pairs) for k in gates},
                evaluations=[item['evaluation'], item['reference']], manifests=[a['manifest'], b['manifest']]))
    return dict(new_training_steps=0, new_evaluation_episodes=512, reused_evaluation_episodes=512,
                successful_new_worker_seconds=worker_seconds, rejected_attempts=4,
                scope='paired development support geometry comparison, no identified contact-physics cause', results=rows)


if __name__ == '__main__':
    result = build_report()
    lines = ['# P2-37 동일 거리 목표의 지지면 비교', '',
             '각 셀은0/5/10/15cm 순서의 성공 수(거리당16개)다. 학습은 추가하지 않았다.', '',
             '| seed | 학습 조건 | deck | continuous (재사용) |', '|---|---|---|---|']
    for seed in range(4):
        for condition in ('chain', 'mixed'):
            group = [r for r in result['results'] if r['seed'] == seed and r['condition'] == condition]
            deck = '/'.join(str(r['deck_successes']) for r in group)
            continuous = '/'.join(str(r['continuous_successes']) for r in group)
            lines.append(f'| {seed} | {condition} | {deck} | {continuous} |')
    (ROOT / 'docs/p2-37-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/p2-37-comparison.md').write_text('\n'.join(lines) + '\n')
    print('Validated all 16 support evaluations and 32 paired distance groups.')
