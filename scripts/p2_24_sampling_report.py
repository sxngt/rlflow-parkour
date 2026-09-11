"""Paired mean/sample evaluation of two families of bounded frozen policies."""
import json
from pathlib import Path
from p2_20_checkpoint_report import restored_distribution

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows, distributions = [], []
    paired = None
    for experiment in ('p2-20', 'p2-24'):
        for seed in range(4):
            train = ROOT/'artifacts'/f'{experiment}-deck-seed{seed}'
            config = json.loads((train/'config.json').read_text())
            distribution = restored_distribution(train, 1600)
            distributions.append({'experiment': experiment, 'seed': seed, **distribution})
            cp = json.loads((train/'checkpoint-001600.json').read_text())
            for mode, rng in [('mean', None), ('sampled', 20000), ('sampled', 20001)]:
                name = train.name+'__final-evaluation' if mode == 'mean' else f"{'p2-23' if experiment == 'p2-20' else 'p2-24'}-{experiment}-seed{seed}-sampled-rng{rng}"
                path = ROOT/'artifacts'/name
                meta = json.loads((path/'run.json').read_text())
                result = json.loads((path/'evaluation.json').read_text())
                scenarios = json.loads((path/'scenarios.json').read_text())['episodes']
                assert meta['status'] == 'SUCCEEDED' and result['episodes'] == len(scenarios) == 64
                paired = scenarios if paired is None else paired
                assert paired == scenarios
                assert meta['checkpoint']['sha256'] == cp['sha256']
                assert meta['checkpoint']['completed_iterations'] == 1600
                assert meta['config']['jump'] == config['jump']
                assert meta['config']['exploration'] == config['exploration']
                assert meta['config']['terrain_contract'] == config['terrain_contract']
                assert meta['action_evaluation']['mode'] == mode and meta['action_evaluation']['seed'] == rng
                rows.append({'experiment': experiment, 'seed': seed, 'mode': mode, 'rng': rng,
                             'run': name, 'reused': mode == 'mean' or experiment == 'p2-20', 'successes': result['successes'],
                             'valid_flights': result['valid_flights'], 'first_touch_precise': result['first_touch_precise_episodes'],
                             'stabilized': result['stabilized_episodes'], 'by_distance': result['by_distance']})
    summary = {'rows': rows, 'distributions': distributions, 'additional_training_steps': 0,
               'scope': 'Fixed development scenarios and checkpoint, mean versus two sampled action RNG repeats. Not a reconstruction of evolving training or independent training replicates.'}
    (ROOT/'docs/p2-24-sampling-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = ['# P2-24 고정 모델 행동 샘플링 진단', '',
             '모든모델은동일64개개발군을사용했다. 각checkpoint의설정일정에따라최종effective std상한(P2-20:0.1/P2-24:0.05)을검증했다. 추가학습0step.', '',
             '| 모델군 | seed | 행동 | RNG | 성공 /64 | 유효비행 | 최초정밀 | 안정화 |',
             '|---|---:|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['experiment']} | {r['seed']} | {r['mode']} | {r['rng']} | {r['successes']} | {r['valid_flights']} | {r['first_touch_precise']} | {r['stabilized']} |")
    lines += ['', 'mean은기존감사완료평가를재사용했다. 행동RNG두개는학습seed두개가아니다. 학습분포·정책업데이트의효과까지분리한결과가아니며모델승격에사용하지않는다.', '']
    (ROOT/'docs/p2-24-sampling-results.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
