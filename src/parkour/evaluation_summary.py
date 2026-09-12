"""Distance summaries from executed scenarios, independent of training goals."""
import copy
import hashlib
import json
import math
from pathlib import Path


def by_distance(records, scenarios):
    if not records or len(records) != len(scenarios):
        raise ValueError('Missing evaluation episodes')
    groups = {}
    seen = set()
    for record, scenario in zip(records, scenarios):
        if record['scenario_id'] != scenario['id'] or scenario['id'] in seen:
            raise ValueError('Scenario identity mismatch or duplicate')
        seen.add(scenario['id'])
        distance = float(scenario['goal_forward_m'])
        actual = float(record['goal_forward_m'])
        if not math.isfinite(distance) or not math.isfinite(actual) or abs(actual-distance) > 1e-6:
            raise ValueError('Executed distance differs from scenario')
        groups.setdefault(distance, []).append(record)
    keys = {'successes': 'success', 'launches_in_region': 'launch_in_region',
            'travel_met': 'distance_requirement_met', 'first_touch_precise': 'first_touch_all_within',
            'stabilized': 'stabilized_once'}
    return {str(distance): {'episodes': len(rows), **{name: sum(bool(r[key]) for r in rows)
            for name, key in keys.items()}} for distance, rows in sorted(groups.items())}


def load_report(directory):
    """Derive a corrected in-memory view; never rewrite archived artifacts."""
    directory = Path(directory)
    path = directory / 'evaluation.json'
    raw = path.read_bytes()
    report = json.loads(raw)
    if (report['results'] and 'goal_forward_m' in report['results'][0]
            and 'distance_requirement_met' in report['results'][0]):
        scenarios_path = directory / 'scenarios.json'
        scenarios_raw = scenarios_path.read_bytes()
        derived = by_distance(report['results'], json.loads(scenarios_raw)['episodes'])
        if report.get('by_distance') != derived:
            report['summary_derivation'] = {'reason': 'Recomputed distance groups from executed scenarios',
                'source_evaluation_sha256': hashlib.sha256(raw).hexdigest(),
                'source_scenarios_sha256': hashlib.sha256(scenarios_raw).hexdigest(),
                'original_by_distance': copy.deepcopy(report.get('by_distance')),
                'scope': 'by_distance only; episode records and aggregate outcomes unchanged'}
        report['by_distance'] = derived
    return report
