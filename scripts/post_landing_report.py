"""Paired 200Hz post-contact target retention; not a reconstruction of success gates."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.diagnostics import jump_first_touches


def longest_span(mask, time):
    indices = np.flatnonzero(mask)
    if not len(indices):
        return 0.
    groups = np.split(indices, np.flatnonzero(np.diff(indices) != 1) + 1)
    return max(float(time[g[-1]] - time[g[0]]) for g in groups)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    paired = None
    rows = []
    conditions = list(dict.fromkeys(r['condition'] for r in spec['runs']))
    fig, axes = plt.subplots(4, len(conditions), figsize=(14, 12), squeeze=False)
    for entry in spec['runs']:
        p = ROOT / 'artifacts' / entry.get('evaluation_run', entry['run'] + '__final-evaluation')
        meta = json.loads((p / 'run.json').read_text())
        evaluation = json.loads((p / 'evaluation.json').read_text())
        scenarios = json.loads((p / 'scenarios.json').read_text())['episodes']
        assert meta['status'] == 'SUCCEEDED' and len(scenarios) == evaluation['episodes'] == 64
        paired = scenarios if paired is None else paired
        assert scenarios == paired
        with np.load(p / 'motion-trace.npz') as archive:
            a = {k: archive[k] for k in ('time', 'valid', 'stage', 'force', 'foot_pos')}
        t = a['time']
        assert np.allclose(np.diff(t), .005)
        radius = meta['config']['jump']['landing_radius_m']
        touches = jump_first_touches(a, meta['nominal_foot_xy_m'], scenarios, radius)
        details = []
        for i, (scenario, touch, result) in enumerate(zip(scenarios, touches, evaluation['results'])):
            assert scenario['id'] == result['scenario_id'] == touch['scenario_id']
            target = np.asarray(meta['nominal_foot_xy_m']) + np.asarray(scenario['foot_offsets_xy_m'])
            xy = a['foot_pos'][:, i, :, :2]
            error = np.linalg.norm(xy - target, axis=-1)
            valid = a['valid'][:, i]
            force = np.linalg.norm(a['force'][:, i], axis=-1)
            per_foot = []
            for foot, name in enumerate(('fl', 'fr', 'rl', 'rr')):
                assert touch['times_s'][foot] is not None, 'This report requires all first contacts'
                assert abs(touch['errors_m'][foot] - result[f'first_touch_error_{name}_m']) < 1e-5
                k = int(np.argmin(np.abs(t - touch['times_s'][foot])))
                after = valid & (np.arange(len(t)) >= k)
                outside = np.flatnonzero(after & (error[:, foot] > radius))
                displacement = np.linalg.norm(np.diff(xy[:, foot], axis=0), axis=-1)
                supported_pairs = after[1:] & after[:-1] & (force[1:, foot] > 2) & (force[:-1, foot] > 2)
                per_foot.append({'name': name, 'first_contact_s': float(t[k]),
                                 'first_error_m': touch['errors_m'][foot],
                                 'first_exit_delay_s': float(t[outside[0]] - t[k]) if len(outside) else None,
                                 'max_error_m': float(error[after, foot].max()),
                                 'terminal_error_m': float(error[np.flatnonzero(valid)[-1], foot]),
                                 'supported_center_path_m': float(displacement[supported_pairs].sum())})
            all_touch = max(touch['times_s'])
            after = valid & (t >= all_touch - 1e-9)
            inside = (error <= radius).all(axis=1)
            window = after & (t <= all_touch + .2 + 1e-9)
            complete_window = float(t[np.flatnonzero(valid)[-1]]) >= all_touch + .2 - 1e-9
            early_exit = bool((window & ~inside).any())
            details.append({'scenario_id': scenario['id'], 'goal_forward_m': result['goal_forward_m'],
                            'success': result['success'], 'stabilized_once': result['stabilized_once'],
                            'all_touch_s': all_touch, 'post_touch_observed_span_s': float(t[np.flatnonzero(valid)[-1]] - all_touch),
                            'max_all_feet_inside_span_s': longest_span(after & inside, t),
                            'window_200ms_complete': complete_window, 'window_200ms_exit_observed': early_exit,
                            'per_foot': per_foot})
            if i == 0:
                ax = axes[entry['seed'], conditions.index(entry['condition'])]
                for foot, name in enumerate(('FL', 'FR', 'RL', 'RR')):
                    ax.plot(t[after] - all_touch, 100 * error[after, foot], label=name)
                ax.axhline(100 * radius, color='black', ls='--')
                ax.set_title(f"{entry['condition']} / seed {entry['seed']} / scenario 0")
                ax.set_xlabel('Time since all first contacts [s]')
                ax.set_ylabel('Foot XY target error [cm]')
                ax.set_xlim(0, .6)
                ax.grid(alpha=.2); ax.legend(ncol=4)
        failed = [d for d in details if not d['stabilized_once']]
        rows.append({**entry, 'evaluation_run': p.name, 'unstabilized': len(failed),
                     'unstabilized_with_exit_200ms': sum(d['window_200ms_exit_observed'] for d in failed),
                     'unstabilized_without_200ms_inside_span': sum(d['max_all_feet_inside_span_s'] < .2 - 1e-9 for d in failed),
                     'details': details})
    stem = spec['report']
    payload = {'rows': rows, 'additional_training_steps': 0,
               'scope': 'Post-hoc paired original traces. First contacts checked against recorded KPI. Continuous 200Hz geometric spans (last-first sample), not 50Hz control dwell/hysteresis/other success gates. Observations are censored when first episode ends. Supported center path is not proven sliding.'}
    (ROOT / f'docs/{stem}-post-landing.json').write_text(json.dumps(payload, indent=2) + '\n')
    for pair in axes:
        low = min(ax.get_ylim()[0] for ax in pair)
        high = max(ax.get_ylim()[1] for ax in pair)
        for ax in pair:
            ax.set_ylim(low, high)
    fig.tight_layout(); fig.savefig(ROOT / f'docs/figures/{stem}-post-landing.png', dpi=150); plt.close(fig)
    lines = [f'# {stem.upper()} 최초 착지 이후 목표 유지', '',
             '동일64개 개발군·200Hz 원본 기록을 비교했다. 발별 최초접촉 오차는 기존 KPI와1e-5m 이내로 대조했다.', '',
             '| 조건 | seed | 안정화 미달 | 그중 첫 접촉 완료 후200ms 안에 영역 이탈 관찰 | 그중 연속200ms 기하 유지 구간 없음 |',
             '|---|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['condition']} | {r['seed']} | {r['unstabilized']} | {r['unstabilized_with_exit_200ms']} | {r['unstabilized_without_200ms_inside_span']} |")
    lines += ['', '영역 유지는 발 중심 XY 오차5cm 기준만을 뜻한다. 50Hz 제어기의 dwell·접촉 hysteresis·자세·속도 판정을 재현한 성공 지표가 아니다. 연속 구간은 마지막과 첫 샘플의 시간 차로 계산한다. 종료 후에는 관측하지 않으므로 성공 episode와 실패 episode의 전체 경로 길이를 무조건 비교하지 않는다. 200ms 창의 관측 완료 여부와 이탈 관찰 여부를 별도로 저장했다. 지지 중 발 중심 이동은 마찰 미끄러짐의 확정 증거가 아니다.', '',
              f'![동일 scenario 0의 발별 오차](figures/{stem}-post-landing.png)', '']
    (ROOT / f'docs/{stem}-post-landing.md').write_text('\n'.join(lines))
    print('\n'.join(lines[:14]))


if __name__ == '__main__':
    main()
