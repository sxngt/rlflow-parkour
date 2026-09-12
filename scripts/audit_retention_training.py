"""Audit completed retention runs against their full per-update task accounting."""
import argparse
import json
from pathlib import Path

from audit_artifacts import audit


def check(path):
    path = Path(path)
    audit(path)
    run = json.loads((path / 'run.json').read_text())
    config = run['config']
    assert config['retention_training']['single_fraction'] == .5
    rows = [json.loads(line) for line in (path / 'metrics.jsonl').read_text().splitlines()]
    expected = config['num_envs'] * config['runner']['num_steps_per_env'] // 2
    exposure = [[0, 0], [0, 0]]
    for row in rows:
        steps = row['task_hop_environment_steps']
        assert len(steps) == 2 and all(len(x) == 2 for x in steps)
        assert all(type(n) is int and n >= 0 for x in steps for n in x)
        assert [sum(x) for x in steps] == [expected, expected]
        assert steps[1][1] == 0
        assert [sum(steps[t][h] for t in range(2)) for h in range(2)] == row['hop_environment_steps']
        assert sum(row['single_goal_environment_steps']) == expected
        goals = config['retention_training']['single_goal_choices_m']
        assert len(row['single_goal_environment_steps']) == len(row['single_goal_reset_draws']) == len(goals)
        for distance, steps_at_goal, draws in zip(goals, row['single_goal_environment_steps'], row['single_goal_reset_draws']):
            key = str(distance)
            assert steps_at_goal <= row['goal_environment_steps'][key]
            assert draws <= row['goal_reset_draws'][key]
            if distance != .15:
                assert steps_at_goal == row['goal_environment_steps'][key]
        assert sum(row['task_episodes']) == row['episodes']
        assert sum(row['task_successes']) == row['successes']
        assert all(s <= n for s, n in zip(row['task_successes'], row['task_episodes']))
        assert all(s <= n for s, n in zip(row['single_goal_reset_draws'], row['goal_reset_draws'].values()))
        for t in range(2):
            for h in range(2):
                exposure[t][h] += steps[t][h]
    return dict(run=str(path), updates=len(rows), first_update=rows[0]['iteration'],
                last_update=rows[-1]['iteration'], new_steps=len(rows) * expected * 2,
                task_hop_environment_steps=exposure,
                task_successes=[sum(r['task_successes'][t] for r in rows) for t in range(2)],
                scope='completed run accounting, not performance or bitwise resume proof')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+')
    args = parser.parse_args()
    for directory in args.directories:
        print(json.dumps(check(directory)))
