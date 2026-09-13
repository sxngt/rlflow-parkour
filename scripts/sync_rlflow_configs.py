"""configs/*.json → configs/*.yaml (RLflow/Hydra 용 1:1 사본, `project: parkour` 추가).

기존 scripts/*.py 는 JSON 을 그대로 쓰고, RLflow 파이프라인(lab-pipeline resolve, train.py --config-name)은 YAML 을 읽는다.
JSON 을 고치면 이 스크립트를 다시 실행해 커밋한다 (CI 가 동기화 여부를 검사한다: --check).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"
SKIP = {"research-tags.json"}     # 태그 registry (실행 config 아님)


def render(path: Path) -> str:
    data = json.loads(path.read_text())
    if "task" not in data:
        raise ValueError(f"{path.name}: not a run config (no 'task')")
    out = {"project": "parkour", **data}
    return "# generated from " + path.name + " by scripts/sync_rlflow_configs.py — edit the JSON, then re-run.\n" + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=200)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="쓰지 않고 차이만 검사 (CI)")
    a = p.parse_args()
    stale: list[str] = []
    for js in sorted(CONFIGS.glob("*.json")):
        if js.name in SKIP:
            continue
        try:
            text = render(js)
        except ValueError as e:
            print(f"skip {e}", file=sys.stderr)
            continue
        ya = js.with_suffix(".yaml")
        if a.check:
            if not ya.exists() or ya.read_text() != text:
                stale.append(ya.name)
        else:
            ya.write_text(text)
    if a.check and stale:
        print("stale yaml configs (run scripts/sync_rlflow_configs.py):", ", ".join(stale), file=sys.stderr)
        return 1
    print("ok" if a.check else f"wrote {len(list(CONFIGS.glob('*.yaml')))} yaml configs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
