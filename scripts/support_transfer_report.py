"""P2-14 paired results and conservative first-touch geometry diagnostics."""
import json
import argparse
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from parkour.diagnostics import jump_first_touches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--include-deck', action='store_true')
    args = parser.parse_args()
    modes = ('flat', 'continuous', 'split', 'deck') if args.include_deck else ('flat', 'continuous', 'split')
    suffix = '-with-deck' if args.include_deck else ''
    rows = []
    paired_scenarios = None
    calibration_hash = None
    for seed in range(4):
        policy_hash = None
        for mode in modes:
            path = ROOT/'artifacts'/f'p2-14-{mode}-seed{seed}'
            meta = json.loads((path/'run.json').read_text())
            report = json.loads((path/'evaluation.json').read_text())
            manifest = json.loads((path/'scenarios.json').read_text())
            assert meta['status'] == 'SUCCEEDED' and report['episodes'] == 64
            support = meta['evaluation_support']
            assert support['mode'] == mode and 'probe_initial_x_offset_m' not in support
            policy_hash = policy_hash or meta['checkpoint']['sha256']
            assert policy_hash == meta['checkpoint']['sha256']
            calibration_hash = calibration_hash or support['reference_sha256']
            assert calibration_hash == support['reference_sha256']
            paired_scenarios = paired_scenarios or manifest['episodes']
            assert paired_scenarios == manifest['episodes']
            with np.load(path/'motion-trace.npz') as archive:
                a = {key: archive[key] for key in ('time', 'valid', 'stage', 'force', 'foot_pos')}
            assert np.allclose(np.diff(a['time']), .005)
            touches = jump_first_touches(a, meta['nominal_foot_xy_m'], manifest['episodes'],
                                         meta['config']['jump']['landing_radius_m'])
            details = []
            for i, touch in enumerate(touches):
                centers, contained = [], []
                for foot, name in enumerate(('fl', 'fr', 'rl', 'rr')):
                    error = touch['errors_m'][foot]
                    original = report['results'][i][f'first_touch_error_{name}_m']
                    assert (error is None and original == -1) or (error is not None and abs(error-original) < 1e-5)
                    t = touch['times_s'][foot]
                    if t is None:
                        centers.append(False); contained.append(False); continue
                    index = int(np.argmin(np.abs(a['time']-t)))
                    x, y, z = a['foot_pos'][index, i, foot]
                    if mode == 'flat':
                        center_ok = extent_ok = bool(abs(z-.02) <= .01)
                    else:
                        surface = support['layout']['surfaces'][0] if mode == 'deck' else next(s for s in support['layout']['surfaces']
                                       if s['foot'] == support['foot_names'][foot]
                                       and s['role'] == ('landing' if mode == 'split' else 'bridge'))
                        x0, x1, y0, y1 = surface['bounds_xy_m']
                        center_ok = bool(x0 <= x <= x1 and y0 <= y <= y1 and abs(z-.02) <= .01)
                        extent_ok = bool(x0+.02 <= x <= x1-.02 and y0+.02 <= y <= y1-.02 and abs(z-.02) <= .01)
                    centers.append(center_ok); contained.append(extent_ok)
                details.append({'scenario_id': touch['scenario_id'],
                    'all_first_centers_on_expected_top': all(centers),
                    'all_first_projected_spheres_contained': all(contained)})
            row = {'seed': seed, 'mode': mode, 'evaluation_run': path.name,
                   'successes': report['successes'], 'episodes': 64,
                   'valid_flights': report['valid_flights'],
                   'failures': sum(r['failure'] for r in report['results']),
                   'timeouts': sum(r['timeout'] for r in report['results']),
                   'first_touch_precise': report['first_touch_precise_episodes'],
                   'stabilized': report['stabilized_episodes'],
                   'first_centers_on_expected_top': sum(d['all_first_centers_on_expected_top'] for d in details),
                   'first_projected_spheres_contained': sum(d['all_first_projected_spheres_contained'] for d in details),
                   'original_success_and_contained': sum(r['success'] and d['all_first_projected_spheres_contained']
                                                          for r, d in zip(report['results'], details)),
                   'geometry_details': details}
            rows.append(row)
    summary = {'rows': rows, 'calibration_sha256': calibration_hash,
               'additional_training_steps': 0,
               'geometry_definition': 'First post-flight >5N contact sample at 200Hz; foot center within expected surface bounds and z=2cm +/-1cm. Contained adds 2cm XY inset for sphere projection. Geometric inference, not contact-pair identity or proof of full-episode support.',
               'scope': 'Four training seeds reported separately; 64 height commands paired across terrain and model. Development transfer pilot, not whole-body 15cm gap crossing.'}
    (ROOT/f'docs/p2-14-summary{suffix}.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = ['# P2-14 고정 정책의 지지면 전이', '',
             '각 행은 동일한 64개 높이 명령을 사용한다. 추가 학습은 0 step이다. 성공은 기존 도약 조건이며 지지면 내부 판정과 구분한다.', '',
             '| seed | 지형 | 기존 성공 | 유효 비행 | 실패 | timeout | 최초 접촉 정밀 | 최초 구 투영 포함 | 성공+포함 |',
             '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['seed']} | {r['mode']} | {r['successes']}/64 | {r['valid_flights']} | {r['failures']} | {r['timeouts']} | {r['first_touch_precise']} | {r['first_projected_spheres_contained']} | {r['original_success_and_contained']} |")
    lines += ['', '구 투영 포함은 200Hz 최초 접촉 시 발 중심의 XY가 표면 경계에서 2cm 이상 안쪽이고 z=2±1cm인지 보는 보수적 기하 진단이다. 실제 접촉 쌍을 직접 확인한 결과나 전체 착지 구간의 지지 보장이 아니다. 평지에는 XY 경계가 없어 높이만 확인한다.', '',
              '원시 진단에서 얻은 최초 접촉 오차를 환경이 저장한 값과 1e-5m 이내로 대조했다. seed별 결과를 유지하며 256개 episode를 독립 학습 seed처럼 집계하지 않는다. 발 목표 전이는 15cm, 분리 발판의 실제 빈 공간은 6cm다.', '']
    if args.include_deck:
        lines += ['', 'deck는 원래 세 조건의 결과 확인 후 별도로 사전 정의한 추가 진단(1.4×1.2m 단일 발판)이다. 원래 결과 문서는 덮어쓰지 않는다.']
    (ROOT/f'docs/p2-14-results{suffix}.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
