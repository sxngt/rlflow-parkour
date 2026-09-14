#!/usr/bin/env python3
"""RLflow 커리큘럼 단계 config 생성.

  python3 scripts/make_stage_config.py --base p3-70-control --name c1-gap50 --fractions '{"base":0.25,"gap":0.5}' \
      --iterations 800 --tags phase:P3 step:c1 condition:gap50 [--set runner.algorithm.learning_rate=0.0001 ...]

base config 의 terrain_contract.layout 을 curriculum_maps.build_mixed_discrete_axes(seed, fractions) 로 바꾸고
configs/<name>.json + .yaml 을 쓴다 (Hydra 는 YAML 을 읽는다). 학습 부모(fork_from)는 config 에 넣지 않고 런 제출 override 로 준다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def set_dotted(d: dict, key: str, value):
    parts = key.split(".")
    for k in parts[:-1]:
        d = d.setdefault(k, {})
    d[parts[-1]] = value


def parse_value(v: str):
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return v


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", required=True, help="configs/<base>.json")
    p.add_argument("--name", required=True)
    p.add_argument("--fractions", required=True, help='JSON: 0.4 또는 {"base":0.25,"gap":0.5} (terrain_mix 사용 시 첫 그룹/호환용 layout)')
    p.add_argument("--mix", help='JSON terrain_mix: {"seeds":[1],"fractions":{"min":0.6,"max":1.0,"count":8}} → env 별 혼합 지형')
    p.add_argument("--geometry-seed", type=int, default=1)
    p.add_argument("--iterations", type=int)
    p.add_argument("--tags", nargs="*", default=[])
    p.add_argument("--set", nargs="*", default=[], help="dotted=value (JSON 값)")
    p.add_argument("--force", action="store_true")
    a = p.parse_args()
    from parkour.curriculum_maps import build_mixed_discrete_axes, describe, normalize_fractions
    from parkour.terrain_contract import training_support

    cfg = json.loads((ROOT / "configs" / f"{a.base}.json").read_text())
    fr = normalize_fractions(json.loads(a.fractions))
    layout = build_mixed_discrete_axes(a.geometry_seed, fr)
    cfg["terrain_contract"]["layout"] = layout
    cfg["terrain_contract"]["geometry_seed"] = a.geometry_seed
    cfg["terrain_contract"].pop("terrain_mix", None)
    if a.mix:
        from parkour.terrain_mix import build_mix, describe_mix, mix_groups
        mix = json.loads(a.mix)
        entries = build_mix(mix)
        cfg["terrain_contract"]["terrain_mix"] = mix
        cfg["terrain_contract"]["layout"] = entries[0]["layout"]          # 호환용: 첫 그룹의 지도
        cfg["terrain_contract"]["geometry_seed"] = entries[0]["seed"]
        print(describe_mix(mix_groups(mix, int(cfg.get("num_envs", 2048)))))
    if a.iterations:
        cfg["iterations"] = a.iterations
    if a.tags:
        cfg["research_tags"] = a.tags
    for kv in a.set:
        k, v = kv.split("=", 1)
        set_dotted(cfg, k, parse_value(v))
    # fork 계약(policy_fork.validate_continuous_fork)은 새 최상위 키를 허용하지 않는다 → 커리큘럼 정보는 태그로만 남긴다
    cfg["research_tags"] = [t for t in cfg.get("research_tags", []) if not t.startswith(("curriculum:", "mix:"))] + ["curriculum:" + ",".join(f"{k}{v:g}" for k, v in fr.items())]
    if a.mix:
        cfg["research_tags"].append("mix:" + ",".join(str(x) for x in json.loads(a.mix)["seeds"]) + ":" + json.dumps(json.loads(a.mix)["fractions"], separators=(",", ":")))
    training_support(cfg)      # 계약 검증 (layout 일관성)
    out = ROOT / "configs" / f"{a.name}.json"
    if out.exists() and not a.force:
        raise SystemExit(f"{out} exists (use --force)")
    out.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    from sync_rlflow_configs import render

    (ROOT / "configs" / f"{a.name}.yaml").write_text(render(out))
    print(f"wrote configs/{a.name}.json/.yaml  fractions={fr} iterations={cfg['iterations']}")
    print(describe(layout, 4, 13))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
