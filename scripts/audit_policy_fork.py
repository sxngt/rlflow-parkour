"""Verify initialization of locally generated policy forks, including live runs.

This validates the immutable initial checkpoint and a snapshot of metrics; it
neither certifies run completion nor replaces the completed-artifact audit.
"""
import argparse
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from parkour.learning import read_checkpoint
from parkour.policy_fork import validate_fork_configs
from parkour.exploration import cap_for_update
from parkour.runtime import sha256


def audit(directory):
    directory = Path(directory)
    meta = json.loads((directory / 'run.json').read_text())
    initial_path = directory / 'checkpoint-000000.pt'
    initial = read_checkpoint(initial_path)
    lineage = meta['lineage']
    assert initial['lineage'] == lineage
    parent_path = Path(lineage['parent_checkpoint']['path'])
    assert sha256(parent_path) == lineage['parent_checkpoint']['sha256']
    parent = read_checkpoint(parent_path)
    config = meta['config']
    assert initial['config'] == config
    validate_fork_configs(parent['config'], config)
    assert initial['completed_iterations'] == initial['total_environment_steps'] == 0
    assert lineage['initial_completed_iterations'] == lineage['initial_environment_steps'] == 0
    assert lineage['parent_completed_iterations'] == parent['completed_iterations']
    assert lineage['parent_environment_steps'] == parent['total_environment_steps']
    assert not initial['optimizer']['state']
    assert initial['learning_rate'] == config['runner']['algorithm']['learning_rate']
    assert all(group['lr'] == initial['learning_rate'] for group in initial['optimizer']['param_groups'])
    for key in ('model', 'normalizer'):
        assert initial[key].keys() == parent[key].keys()
        for name, value in initial[key].items():
            assert torch.isfinite(value).all()
            if key == 'model' and name in ('std_cap', 'std_floor'):
                expected = cap_for_update(config, 0) if name == 'std_cap' else config['exploration']['min_std']
                assert torch.allclose(value, torch.full_like(value, expected), atol=1e-7, rtol=0)
            else:
                assert torch.equal(value, parent[key][name]), (key, name)
    assert lineage['initial_std_cap'] == cap_for_update(config, 0)
    # A live writer may have an unfinished last line; include only committed lines.
    raw = (directory / 'metrics.jsonl').read_bytes()
    metrics = [json.loads(line) for line in raw.split(b'\n')[:-1] if line]
    assert metrics
    steps_per_update = config['num_envs'] * config['runner']['num_steps_per_env']
    for iteration, row in enumerate(metrics, 1):
        assert row['iteration'] == iteration
        assert row['total_environment_steps'] == iteration * steps_per_update
        assert abs(row['exploration_std_cap'] - cap_for_update(config, iteration - 1)) < 1e-7
    return {'run': str(directory), 'scope': 'fork initialization and observed metrics only',
            'initial_checkpoint_sha256': sha256(initial_path),
            'parent_checkpoint': lineage['parent_checkpoint'],
            'observed_updates': len(metrics), 'observed_new_steps': metrics[-1]['total_environment_steps'],
            'audit': 'passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directories', nargs='+', type=Path)
    args = parser.parse_args()
    for directory in args.directories:
        print(json.dumps(audit(directory)), flush=True)
