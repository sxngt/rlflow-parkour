"""Verify every P2-34 result archive and summarize observed failure gates."""
import hashlib
import json
from pathlib import Path

from p2_34_evaluate import evaluation_plan
from p2_32_failure_report import analyze

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def main():
    records = []
    for item in evaluation_plan():
        source = ROOT / item['evaluation']
        matches = list((ROOT / 'result').glob(f'*__{source.name}/manifest.json'))
        assert len(matches) == 1, (source, matches)
        manifest = matches[0]
        record = json.loads(manifest.read_text())
        replay = json.loads((source / 'replay.json').read_text())
        assert record['evaluation_run'] == source.name
        assert record['training_run'] == Path(item['source']).name
        assert {'phase:P2', 'step:p2-34-chain-training'} <= set(record['research_tags'])
        assert record['title'] and len(record['video_episodes']) == 64
        assert replay['camera']['framing_side'] == 4
        assert len(replay['visible_env_ids']) == 64
        assert digest(manifest.parent / record['video']) == record['source_video_sha256']
        events = source / 'chain-events.json'
        if events.exists():
            archive = record['chain_events']
            assert digest(events) == digest(manifest.parent / archive['file']) == archive['sha256']
        report = json.loads((source / 'evaluation.json').read_text())
        gates = ('valid_flight', 'launch_in_region', 'travel_requirement_met',
                 'first_touch_all_within', 'final_all_feet_in_radius', 'stabilized_once')
        row = {k: item[k] for k in ('seed', 'condition', 'suite', 'evaluation')}
        row.update(manifest=str(manifest.relative_to(ROOT)), title=record['title'],
                   video_sha256=record['source_video_sha256'],
                   terminal_gate_false_counts={key: sum(not r[key] for r in report['results']) for key in gates})
        if item['suite'] == 'chain':
            row['second_hop_diagnosis'] = analyze(source)
        records.append(row)
    out = ROOT / 'artifacts/p2-34-archive-diagnosis.json'
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    print(f'Verified {len(records)} archived videos, tags, framing, and event hashes: {out}')


if __name__ == '__main__':
    main()
