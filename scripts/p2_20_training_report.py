"""Compare completed fixed-budget training stages; never mix in partial runs."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = []
    onsets = []
    for experiment in ('p2-18', 'p2-20'):
        for seed in range(4):
            path = ROOT / 'artifacts' / f'{experiment}-deck-seed{seed}'
            run = json.loads((path / 'run.json').read_text())
            metrics = [json.loads(line) for line in (path / 'metrics.jsonl').read_text().splitlines()]
            assert run['status'] == 'SUCCEEDED', path
            assert [m['iteration'] for m in metrics] == list(range(1, 1601))
            assert metrics[-1]['total_environment_steps'] == 39321600
            assert all(math.isfinite(v) for m in metrics for v in m['losses'].values())
            if experiment == 'p2-20':
                for m in metrics:
                    cap = .35 if m['iteration'] <= 800 else .2 if m['iteration'] <= 1200 else .1
                    assert m['exploration_std_cap'] == cap
                    assert .05 - 1e-7 <= m['exploration_std_min'] <= m['exploration_std_max'] <= cap + 1e-7
            onsets.append({'experiment': experiment, 'seed': seed,
                           'first_success_update': next((m['iteration'] for m in metrics if m['successes']), None)})
            for start in (1, 401, 801, 1201):
                stage = metrics[start - 1:start + 399]
                row = {'experiment': experiment, 'seed': seed, 'updates': [start, start + 399]}
                for key in ('episodes', 'successes', 'valid_flights', 'failures'):
                    row[key] = sum(m[key] for m in stage)
                row['success_fraction'] = row['successes'] / row['episodes'] if row['episodes'] else None
                rows.append(row)
    payload = {'rows': rows, 'success_onsets': onsets,
               'scope': 'Training episodes under changing curriculum, sampled actions and evolving policy; not fixed-scenario evaluation. Curriculum resets can discard unfinished episodes. No causal attribution to a single schedule boundary.'}
    (ROOT / 'docs/p2-20-training-stages.json').write_text(json.dumps(payload, indent=2) + '\n')
    lines = ['# P2-20 훈련 단계 비교', '',
             '각 조건은 4개 학습 seed, seed당 39,321,600 환경 step이다. P2-18은 기존 결과를 재사용했다.', '',
             '| 조건 | seed | update | 완료 episode | 유효 비행 | 성공 | 성공 비율 |',
             '|---|---:|---|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['experiment']} | {r['seed']} | {r['updates'][0]}–{r['updates'][1]} | {r['episodes']} | {r['valid_flights']} | {r['successes']} | {r['success_fraction']:.3%} |")
    lines += ['', '이는 변화하는 정책과 목표 분포에서 수집한 훈련 episode 통계다. 고정 평가군 성공률과 구분한다. 커리큘럼 전환은 진행 중 episode를 초기화할 수 있다. 상한 전환 시점에는 목표 거리 또는 출발 반경도 바뀌므로, 경계 전후 변화만으로 탐색 상한의 효과를 확정하지 않는다.', '']
    (ROOT / 'docs/p2-20-training-stages.md').write_text('\n'.join(lines))
    print(json.dumps(onsets))


if __name__ == '__main__':
    main()
