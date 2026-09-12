"""Audit first-episode chain events against independent 200Hz trace samples."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
from audit_artifacts import audit


def check(directory):
    directory = Path(directory)
    audit(directory)
    read = lambda name: json.loads((directory / name).read_text())
    run, report, events = read('run.json'), read('evaluation.json'), read('chain-events.json')
    scenarios = read('scenarios.json')
    contract = run['chain_contract']
    assert contract == report['chain_contract'] == events['contract'] == scenarios['chain_contract']
    count, hops = report['episodes'], contract['hops']
    with np.load(directory / 'motion-trace.npz') as archive:
        trace = {key: archive[key] for key in archive.files}
    assert np.allclose(np.diff(trace['time']), .005, atol=1e-8)
    rows = []
    assert all(0 <= h['env_index'] < count for h in events['hops'])
    assert all(0 <= t['env_index'] < count for t in events['transitions'])
    for i, result in enumerate(report['results']):
        local = [h for h in events['hops'] if h['env_index'] == i]
        transitions = [t for t in events['transitions'] if t['env_index'] == i]
        assert [h['segment'] for h in local] == list(range(len(local)))
        assert 1 <= len(local) <= hops
        assert len(transitions) == len(local) - 1
        assert result['length'] == local[-1]['episode_step']
        assert result['completed_hops'] == sum(h['metrics']['success'] for h in local)
        assert result['success'] == (result['completed_hops'] == hops)
        assert all(h['metrics']['success'] for h in local[:-1])
        assert all(0 < h['local_steps'] <= 200 for h in local)
        assert result['length'] <= 200 * hops
        assert int(trace['valid'][:, i].sum()) == result['length'] * 4
        for h in local:
            m = h['metrics']
            if contract.get('spacing_contract') == 'nonuniform_horizontal_v1':
                assert abs(m['goal_forward_m']-contract['step_lengths_m'][h['segment']]) < 1e-6
            if contract.get('height_contract'):
                sample=h['episode_step']*4-1
                height=contract['support_heights_m'][h['segment']+1]
                assert np.allclose(trace['target_z'][sample,i],height+.02,atol=2e-6,rtol=0)
                expected_error=trace['root_z'][sample,i]-run['stance_calibration']['root_state'][2]-height
                assert abs(m['final_height_error_m']-expected_error)<2e-6
            if m['success']:
                gates = ('valid_flight', 'launch_in_region', 'first_touch_all_within', 'precise_stabilized_once')
                assert all(m[k] for k in gates)
                if contract.get('progress_criterion') == 'mapped_contact_v1':
                    from parkour.support_geometry import expected_goal_surface
                    assert m['mapped_contact_ok']
                    sample = h['episode_step'] * 4 - 1
                    for foot, name in enumerate(('fl','fr','rl','rr')):
                        surface = expected_goal_surface(run['evaluation_support'], foot,
                            run['nominal_foot_xy_m'][foot], contract['absolute_forward_targets_m'][h['segment']])
                        x0,x1,y0,y1 = surface['bounds_xy_m']
                        assert x0 <= m['first_touch_x_'+name] <= x1
                        assert y0 <= m['first_touch_y_'+name] <= y1
                        x,y,z = trace['foot_pos'][sample,i,foot]
                        assert x0 <= x <= x1 and y0 <= y <= y1 and surface['top_z_m'] <= z <= surface['top_z_m']+.04
                        assert trace['force'][sample,i,foot,2] > 2
                else:
                    assert m['travel_requirement_met']
        displacements = []
        for j, transition in enumerate(transitions):
            step = transition['episode_step']
            assert step == local[j]['episode_step']
            assert transition['segment'] == j + 1
            assert all(transition['preserved_tensors_exact'].values())
            sample = step * 4 - 1
            origin = np.asarray(transition['launch_origin_xy_m'])
            assert np.allclose(trace['root_xy'][sample, i], origin, atol=1e-7, rtol=0)
            assert trace['segment'][sample, i] == j
            assert trace['segment'][sample + 1, i] == j + 1
            assert trace['segment_start_step'][sample + 1, i] == step
            assert np.allclose(trace['launch_origin_xy'][sample + 1, i], origin, atol=1e-7, rtol=0)
            expected = np.asarray(run['nominal_foot_xy_m']) + [contract['absolute_forward_targets_m'][j + 1], 0]
            assert np.allclose(transition['target_xy_m'], expected, atol=2e-6, rtol=0)
            assert np.allclose(trace['target_xy'][sample + 1, i], expected, atol=2e-6, rtol=0)
            prep_steps = round(run['config']['jump']['settle_seconds'] / .02)
            prep_end = min((step + prep_steps) * 4, local[j + 1]['episode_step'] * 4)
            prep_actions = trace['action'][sample + 1:prep_end, i]
            if contract.get('settle_command', 'default') == 'hold-last':
                expected_action = trace['action'][sample, i]
            else:
                expected_action = np.zeros_like(trace['action'][sample, i])
            assert len(prep_actions) > 0
            assert np.array_equal(prep_actions, np.broadcast_to(expected_action, prep_actions.shape))
            m = local[j + 1]['metrics']
            if m['launch_recorded']:
                launch = np.array([m['launch_root_x_m'], m['launch_root_y_m']])
                distance = float(np.linalg.norm(launch - origin))
                assert bool(m['launch_in_region']) == (distance <= run['config']['jump']['launch_radius_m'])
                displacements.append(distance)
        rows.append({'scenario_id': result['scenario_id'], 'completed_hops': result['completed_hops'],
                     'transition_count': len(transitions), 'subsequent_launch_displacements_m': displacements})
    return {'run': str(directory), 'audit': 'passed', 'episodes': count, 'successes': report['successes'],
            'transitions': len(events['transitions']), 'results': rows,
            'scope': 'event/trace consistency and runtime preserved-tensor checks; no claim of general policy robustness'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    results = [check(path) for path in args.directories]
    args.out.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps([{k: v for k, v in r.items() if k != 'results'} for r in results]))
