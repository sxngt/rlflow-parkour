"""Separate P2-32 launch drift and post-contact target retention failures."""
import json
from pathlib import Path

import numpy as np


def analyze(directory):
    directory = Path(directory)
    read = lambda name: json.loads((directory / name).read_text())
    events, run = read('chain-events.json'), read('run.json')
    trace = np.load(directory / 'motion-trace.npz')
    spec = run['config']['jump']
    rows = []
    for transition in events['transitions']:
        i, start = transition['env_index'], transition['episode_step']
        hop = next(h for h in events['hops'] if h['env_index'] == i and h['segment'] == 1)
        m, end = hop['metrics'], hop['episode_step']
        assert end > start
        prep_end = start + round(spec['settle_seconds'] / .02)
        assert prep_end <= end
        origin = np.asarray(transition['launch_origin_xy_m'])
        prep_xy = trace['root_xy'][prep_end * 4 - 1, i]
        launch = np.array([m['launch_root_x_m'], m['launch_root_y_m']])
        final_errors = np.linalg.norm(trace['foot_pos'][end * 4 - 1, i, :, :2] -
                                      trace['target_xy'][end * 4 - 1, i], axis=1)
        assert bool((final_errors <= spec['landing_radius_m']).all()) == m['final_all_feet_in_radius']
        rows.append({
            'env_index': i, 'success': m['success'], 'failure': m['failure'], 'timeout': m['timeout'],
            'prep_body_delta_xy_m': (prep_xy - origin).tolist(),
            'prep_body_displacement_m': float(np.linalg.norm(prep_xy - origin)),
            'launch_after_prep_delta_xy_m': (launch - prep_xy).tolist() if m['launch_recorded'] else None,
            'launch_displacement_m': float(np.linalg.norm(launch - origin)) if m['launch_recorded'] else None,
            'launch_in_region': m['launch_in_region'],
            'first_touch_errors_m': [m['first_touch_error_' + foot + '_m'] for foot in ('fl', 'fr', 'rl', 'rr')],
            'final_foot_errors_m': final_errors.tolist(),
            'final_feet_outside': [name for name, error in zip(('FL', 'FR', 'RL', 'RR'), final_errors)
                                   if error > spec['landing_radius_m']],
            'final_gates': {
                'first_touch_precise': m['first_touch_all_within'],
                'travel': m['travel_requirement_met'],
                'apex': m['flight_apex_rise_m'] >= m['required_apex_m'],
                'foot_radius': m['final_all_feet_in_radius'],
                'supported': m['final_supported'] and m['final_contact_all'],
                'height': abs(m['final_height_error_m']) <= spec['final_height_error_max_m'],
                'vertical_speed': abs(m['final_vz_m_s']) <= spec['final_vz_max_m_s'],
                'angular_speed': m['final_angular_speed_rad_s'] <= spec['final_angular_speed_max_rad_s'],
            },
        })
    return {'run': str(directory), 'second_attempts': len(rows),
            'terminal_gate_failure_counts': {key: sum(not r['final_gates'][key] for r in rows)
                                            for key in rows[0]['final_gates']} if rows else {},
            'scope': 'terminal gates and interval displacement; foot-center drift is not proof of physical slip',
            'results': rows}


if __name__ == '__main__':
    results = [analyze(f'artifacts/p2-32-chain-two-hop-seed{s}') for s in range(4)]
    Path('docs/p2-32-failure-diagnosis.json').write_text(json.dumps(results, indent=2) + '\n')
    for result in results:
        print(result['run'], result['terminal_gate_failure_counts'])
