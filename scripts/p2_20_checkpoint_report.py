"""Compare frozen P2-20 checkpoints on one paired final-condition development set."""
import json
import sys
from pathlib import Path
import torch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from parkour.exploration import BoundedActorCritic


def restored_distribution(train, update):
    data = torch.load(train/f'checkpoint-{update:06d}.pt', map_location='cpu', weights_only=False)
    config = data['config']
    cfg = dict(config['runner']['policy'])
    assert cfg.pop('class_name') == 'ActorCritic'
    obs_dim = data['model']['actor.0.weight'].shape[1]
    policy = BoundedActorCritic(obs_dim, obs_dim, 12, min_std=.05, max_std=.35, **cfg)
    policy.load_state_dict(data['model'])
    policy.eval()
    policy.update_distribution(torch.zeros(1, obs_dim))
    cap = {800: .35, 1200: .2, 1600: .1}[update]
    assert abs(float(policy.std_cap)-cap) < 1e-7
    assert abs(float(policy.std_floor)-.05) < 1e-7
    std = policy.distribution.stddev.detach()
    assert torch.isfinite(std).all() and float(std.min()) >= .05-1e-7 and float(std.max()) <= cap+1e-7
    return {'stored_cap': float(policy.std_cap), 'effective_std_min': float(std.min()),
            'effective_std_max': float(std.max()), 'effective_std_mean': float(std.mean())}


def main():
    rows, paired = [], None
    for seed in range(4):
        train = ROOT/'artifacts'/f'p2-20-deck-seed{seed}'
        config = json.loads((train/'config.json').read_text())
        for update in (800, 1200, 1600):
            suffix = '__final-evaluation' if update == 1600 else f'__checkpoint-{update:06d}-evaluation'
            path = train.with_name(train.name+suffix)
            meta = json.loads((path/'run.json').read_text())
            report = json.loads((path/'evaluation.json').read_text())
            scenarios = json.loads((path/'scenarios.json').read_text())['episodes']
            assert meta['status'] == 'SUCCEEDED' and len(scenarios) == report['episodes'] == 64
            paired = scenarios if paired is None else paired
            assert paired == scenarios and meta['config']['jump']['launch_radius_m'] == .03
            assert meta['config']['jump'] == config['jump']
            side = json.loads((train/f'checkpoint-{update:06d}.json').read_text())
            assert meta['checkpoint']['sha256'] == side['sha256']
            assert meta['checkpoint']['completed_iterations'] == update
            distribution = restored_distribution(train, update)
            rows.append({'seed': seed, 'update': update, 'evaluation_run': path.name,
                         'restored_distribution': distribution,
                         'checkpoint_sha256': side['sha256'], 'successes': report['successes'],
                         'valid_flights': report['valid_flights'],
                         'first_touch_precise': report['first_touch_precise_episodes'],
                         'stabilized': report['stabilized_episodes'], 'by_distance': report['by_distance']})
    summary = {'rows': rows, 'additional_training_steps': 0,
               'scope': 'Post-hoc development diagnosis, fixed final 3cm launch radius and paired distance/height commands. Does not isolate effects of each curriculum change.'}
    (ROOT/'docs/p2-20-checkpoint-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = ['# P2-20 중간 모델의 고정 조건 평가', '',
             '모든 모델을 최종3cm 출발 반경·동일64개 개발 episode에서 평가했다. 추가 학습0step. 중간 모델의 당시 훈련 분포와 다른 조건이며 개별 커리큘럼 변경의 인과효과는 분리하지 못한다.', '',
             '| seed | update | 성공 /64 | 유효 비행 | 첫 접촉 정밀 | 안정화 | 거리별 성공 (0/5/10/15cm, 각 /16) |',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in rows:
        dist = '/'.join(str(v['successes']) for k,v in sorted(r['by_distance'].items(),key=lambda x:float(x[0])))
        lines.append(f"| {r['seed']} | {r['update']} | {r['successes']} | {r['valid_flights']} | {r['first_touch_precise']} | {r['stabilized']} | {dist} |")
    lines += ['', '최종보다 중간 모델이 우수하더라도 이 집합으로 고르면 개발 모델 선택이다. 독립 최종 시험 결과나 통계적 유의성을 주장하지 않는다.', '']
    (ROOT/'docs/p2-20-checkpoint-results.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
