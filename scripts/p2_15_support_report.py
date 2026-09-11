"""Audit mixed-distance first contacts against finite support geometry."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.diagnostics import jump_first_touches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', nargs='?', type=Path, default=ROOT / 'configs/reports/p2-15.json')
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text())
    prefix = spec['report']
    if Path(prefix).name != prefix:
        raise ValueError('Report prefix must be a filename component')
    rows, paired, calibration, policies = [], None, None, {}
    for item in spec['runs']:
        path = ROOT / 'artifacts' / item.get('evaluation_run', item['run']+'__final-evaluation')
        meta = json.loads((path / 'run.json').read_text())
        report = json.loads((path / 'evaluation.json').read_text())
        scenarios = json.loads((path / 'scenarios.json').read_text())['episodes']
        assert meta['status'] == 'SUCCEEDED' and len(scenarios) == report['episodes'] == 64
        distances = [r['goal_forward_m'] for r in report['results']]
        rounded = [round(value, 2) for value in distances]
        assert np.allclose(distances, rounded, atol=1e-7, rtol=0)
        assert Counter(rounded) == {0.: 16, .05: 16, .1: 16, .15: 16}
        paired = scenarios if paired is None else paired
        assert paired == scenarios
        support = meta['evaluation_support']
        assert support['mode'] in ('flat', 'deck') and support['matched_material']
        calibration = calibration or support['reference_sha256']
        assert calibration == support['reference_sha256']
        policies.setdefault(item['run'], meta['checkpoint']['sha256'])
        assert policies[item['run']] == meta['checkpoint']['sha256']
        with np.load(path / 'motion-trace.npz') as archive:
            trace = {key: archive[key] for key in ('time', 'valid', 'stage', 'force', 'foot_pos')}
        assert np.allclose(np.diff(trace['time']), .005)
        touches = jump_first_touches(trace, meta['nominal_foot_xy_m'], scenarios,
                                     meta['config']['jump']['landing_radius_m'])
        details = []
        for i, touch in enumerate(touches):
            result = report['results'][i]
            assert result['scenario_id'] == touch['scenario_id']
            inside = []
            for foot, name in enumerate(('fl', 'fr', 'rl', 'rr')):
                error = touch['errors_m'][foot]
                original = result[f'first_touch_error_{name}_m']
                assert (error is None and original == -1) or (error is not None and abs(error-original) < 1e-5)
                time = touch['times_s'][foot]
                if time is None:
                    inside.append(False)
                    continue
                index = int(np.argmin(np.abs(trace['time'] - time)))
                x, y, z = trace['foot_pos'][index, i, foot]
                contained = abs(z - .02) <= .01
                if support['mode'] == 'deck':
                    x0, x1, y0, y1 = support['layout']['surfaces'][0]['bounds_xy_m']
                    contained &= x0+.02 <= x <= x1-.02 and y0+.02 <= y <= y1-.02
                inside.append(bool(contained))
            details.append({'scenario_id': result['scenario_id'], 'goal_forward_m': result['goal_forward_m'],
                            'success': result['success'], 'contained_per_foot': inside,
                            'success_and_contained': bool(result['success'] and all(inside))})
        rows.append({**item, 'successes': report['successes'],
                     'success_and_contained': sum(d['success_and_contained'] for d in details),
                     'all_first_spheres_contained': sum(all(d['contained_per_foot']) for d in details),
                     'by_distance': report['by_distance'], 'details': details})
    summary = {'rows': rows, 'calibration_sha256': calibration, 'policy_hashes': policies,
               'definition': 'First >5N post-flight sample at 200Hz; sphere center z=2±1cm and XY at least 2cm inside deck bounds. Flat has no XY bounds. Geometric inference, not contact-pair identity or sustained support.',
               'additional_training_steps': 0}
    (ROOT / f'docs/{prefix}-support-diagnosis.json').write_text(json.dumps(summary, indent=2)+'\n')
    lines = [f'# {prefix.upper()} 최초 착지 지지면 진단', '',
             '거리 0/5/10/15cm × 높이 명령 16개의 동일 개발군을 사용한다. 원시 200Hz 최초 접촉 오차를 저장된 KPI와 1e-5m 이내로 대조했다.', '',
             '| 조건 | seed | 기존 성공 / 64 | 첫 접촉 네 발 투영 포함 | 성공과 포함 모두 |',
             '|---|---:|---:|---:|---:|']
    for row in rows:
        lines.append(f"| {row['condition']} | {row['seed']} | {row['successes']} | {row['all_first_spheres_contained']} | {row['success_and_contained']} |")
    lines += ['', '포함은 발 중심 높이 2±1cm 및 발판 가장자리에서 2cm 여유를 확인한 기하 진단이다. 실제 접촉 쌍이나 착지 이후 지지 지속을 보장하지 않는다. 평지에는 XY 경계가 없다. 이 진단은 기존 성공 정의를 소급 변경하지 않는다.', '']
    (ROOT / f'docs/{prefix}-support-diagnosis.md').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
