"""Paired frozen-policy preparation-command comparison; no training budget."""
import json
from pathlib import Path

import numpy as np
from audit_chained_evaluation import check
from p2_32_failure_report import analyze


def read(path, name):
    return json.loads((path / name).read_text())


def main():
    rows = []
    for seed in range(4):
        base = Path(f'artifacts/p2-32-chain-two-hop-seed{seed}')
        trial = Path(f'artifacts/p2-33-hold-last-seed{seed}')
        reports = [read(p, 'evaluation.json') for p in (base, trial)]
        runs = [read(p, 'run.json') for p in (base, trial)]
        assert runs[0]['checkpoint']['sha256'] == runs[1]['checkpoint']['sha256']
        assert read(base, 'scenarios.json')['episodes'] == read(trial, 'scenarios.json')['episodes']
        assert runs[0]['evaluation_support'] == runs[1]['evaluation_support']
        configs = [dict(r['config']) for r in runs]
        for config in configs:
            config.pop('research_tags', None)
        assert configs[0] == configs[1]
        events = [read(p, 'chain-events.json')['hops'] for p in (base, trial)]
        first = [[h for h in es if h['segment'] == 0] for es in events]
        first = [sorted(es, key=lambda h: h['env_index']) for es in first]
        changed_first = sum(a != b for a, b in zip(*first))
        assert len(first[0]) == len(first[1]) == 64
        outcomes = {}
        for label, path, report in zip(('default', 'hold_last'), (base, trial), reports):
            audit = check(path)
            diagnosis = analyze(path)
            attempted = diagnosis['results']
            outcomes[label] = {'course_successes': report['successes'],
                'first_successes': report['episodes'] - report['completed_hops_histogram']['0'],
                'transitions': audit['transitions'],
                'second_launch_outside': sum(not r['launch_in_region'] for r in attempted),
                'terminal_gate_failure_counts': diagnosis['terminal_gate_failure_counts'],
                'mean_preparation_displacement_m': float(np.mean([r['prep_body_displacement_m'] for r in attempted])) if attempted else None,
                'diagnosis': diagnosis}
        rows.append({'seed': seed, 'paired_scenarios': 64, 'new_training_steps': 0,
                     'first_hop_event_differences': changed_first, **outcomes})
    Path('docs/p2-33-comparison.json').write_text(json.dumps(rows, indent=2) + '\n')
    for row in rows:
        print(row['seed'], 'first-hop differences', row['first_hop_event_differences'],
              [(k, row[k]['course_successes'], row[k]['mean_preparation_displacement_m'])
               for k in ('default', 'hold_last')])


if __name__ == '__main__':
    main()
