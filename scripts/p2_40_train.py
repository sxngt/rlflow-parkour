"""Four-seed weighted-target experiment, gated by completed runtime and archive checks."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit
from audit_retention_training import check
from audit_chained_evaluation import check as check_evaluation
from p2_34_archive_audit import digest

ROOT = Path(__file__).resolve().parents[1]

def gates():
    records = []
    for name, updates, first in [('weighted-training-smoke', 12, 1),
                                 ('weighted-training-resume', 2, 13),
                                 ('uniform-regression-smoke', 12, 1),
                                 ('weighted-profile-seed2', 60, 1)]:
        path = ROOT / ('artifacts/p2-40-' + name)
        result = check(path)
        assert result['updates'] == updates and result['first_update'] == first
        evaluation = path.with_name(path.name + '__final-evaluation')
        check_evaluation(evaluation)
        manifests = list((ROOT / 'result').glob('*__' + evaluation.name + '/manifest.json'))
        assert len(manifests) == 1
        manifest = json.loads(manifests[0].read_text())
        run = json.loads((evaluation / 'run.json').read_text())
        assert manifest['checkpoint'] == run['checkpoint']
        assert digest(manifests[0].parent / manifest['video']) == manifest['source_video_sha256']
        event = manifest['chain_events']
        assert digest(manifests[0].parent / event['file']) == digest(evaluation / 'chain-events.json') == event['sha256']
        replay = json.loads((evaluation / 'replay.json').read_text())
        assert len(manifest['video_episodes']) == len(replay['visible_env_ids']) == 64
        assert replay['camera']['framing_side'] == 4
        if name != 'uniform-regression-smoke':
            assert '1:1:1:3' in manifest['title']
            assert {'phase:P2', 'step:p2-40-long-goal-weight'} <= set(manifest['research_tags'])
        result['manifest'] = str(manifests[0].relative_to(ROOT))
        records.append(result)
    config = json.loads((ROOT / 'configs/p2-40-weighted.json').read_text())
    assert config['iterations'] == 800 and config['num_envs'] == 1024
    assert config['runner']['num_steps_per_env'] == 24
    assert config['retention_training']['single_goal_choices_m'] == [0., .05, .1, .15]
    for seed in range(4):
        baseline = ROOT / f'artifacts/p2-39-coverage-seed{seed}'
        audited = check(baseline)
        assert audited['updates'] == 800 and audited['new_steps'] == 19660800
        old = json.loads((baseline / 'config.json').read_text())
        new = copy.deepcopy(config)
        for c in (old, new):
            c.pop('research_tags', None)
            c.pop('seed', None)
        assert old['retention_training']['single_goal_choices_m'] == [0., .05, .1, .15]
        assert 'single_goal_weights' not in old['retention_training']
        assert new['retention_training'].pop('single_goal_weights') == [1, 1, 1, 3]
        assert old == new
        audit(ROOT / f'artifacts/p2-31-mixed-seed{seed}')
    return records


def worker(seed):
    source = f'artifacts/p2-40-weighted-seed{seed}'
    cmd = [sys.executable, 'scripts/run_job.py', '--gpu', str(seed), '--timeout', '2400',
           'train', '--config', 'configs/p2-40-weighted.json', '--seed', str(seed),
           '--fork-from', f'artifacts/p2-31-mixed-seed{seed}/checkpoint-000800.pt', '--out', source]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        checked = check(ROOT / source)
        assert checked['updates'] == 800 and checked['new_steps'] == 19660800
        check_evaluation(ROOT / (source + '__final-evaluation'))
    return dict(seed=seed, exit_code=result.returncode)


if __name__ == '__main__':
    records = gates()
    (ROOT / 'artifacts/p2-40-training-gates.json').write_text(json.dumps(records, indent=2) + '\n')
    for seed in range(4):
        path = ROOT / f'artifacts/p2-40-weighted-seed{seed}'
        if path.exists() or path.with_suffix('.log').exists():
            raise RuntimeError(f'Existing attempt: {path}')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(worker, range(4)))
    print(json.dumps(results), flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
