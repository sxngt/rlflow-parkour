"""Audit first-episode chain events against independent 200Hz trace samples."""
import argparse
import json
from pathlib import Path

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
    trace = np.load(directory / 'motion-trace.npz')
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
            if m['success']:
                assert all(m[k] for k in ('valid_flight', 'launch_in_region',
                    'travel_requirement_met', 'first_touch_all_within', 'precise_stabilized_once'))
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
