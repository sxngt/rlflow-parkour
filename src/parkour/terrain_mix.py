"""Per-environment terrain mixture for the continuous Tracker (RLflow campaign, 2026-09-15).

One training run, many maps: environments are split into contiguous groups and each group gets its own
mixed-discrete layout (geometry seed × difficulty fractions). PPO then learns across the whole difficulty
distribution at once instead of one fixed map per run, which removes the "cliff" collapses of the
single-map curriculum and lets held-out seeds be evaluated for generalization.

terrain_contract.terrain_mix = {
  "seeds": [1, 2, 3],                                  # geometry seeds (each seed × each fraction = one layout)
  "fractions": [0.6, 0.7, 0.8, 0.9, 1.0]               # or {"min": 0.6, "max": 1.0, "count": 8}
                                                       # each entry may also be a per-axis dict {"base":.., "gap":..}
  "weights": null                                      # optional per-layout env share (default equal)
}
All layouts must have the same surface count (mixed_discrete: 25) so per-env tensors stack.
"""
from __future__ import annotations

import copy
import math

from parkour.curriculum_maps import build_mixed_discrete_axes, normalize_fractions


def expand_fractions(spec) -> list:
    if isinstance(spec, dict) and "count" in spec:
        lo, hi, n = float(spec["min"]), float(spec["max"]), int(spec["count"])
        if n < 1 or not 0 <= lo <= hi <= 1:
            raise ValueError("terrain_mix.fractions range invalid")
        return [round(lo + (hi - lo) * i / max(1, n - 1), 4) for i in range(n)] if n > 1 else [lo]
    if isinstance(spec, list) and spec:
        return spec
    raise ValueError("terrain_mix.fractions must be a list or {min,max,count}")


def build_mix(spec: dict) -> list[dict]:
    """→ [{seed, fractions, layout}] in a fixed order (seed-major)."""
    if not isinstance(spec, dict) or not spec.get("seeds"):
        raise ValueError("terrain_mix needs seeds")
    out = []
    for seed in spec["seeds"]:
        for fr in expand_fractions(spec["fractions"]):
            norm = normalize_fractions(fr)
            out.append({"seed": int(seed), "fractions": norm, "layout": build_mixed_discrete_axes(int(seed), norm)})
    counts = {len(e["layout"]["surfaces"]) for e in out}
    if len(counts) != 1:
        raise ValueError(f"terrain_mix layouts differ in surface count {counts}")
    return out


def mix_groups(spec: dict, num_envs: int) -> list[dict]:
    """Contiguous env ranges per layout. Equal shares unless weights are given; remainder goes to the last groups."""
    entries = build_mix(spec)
    k = len(entries)
    if num_envs < k:
        raise ValueError(f"terrain_mix has {k} layouts but only {num_envs} envs")
    weights = spec.get("weights") or [1.0] * k
    if len(weights) != k or any(w <= 0 for w in weights):
        raise ValueError("terrain_mix.weights must match layouts and be positive")
    total = sum(weights)
    sizes = [max(1, int(num_envs * w / total)) for w in weights]
    i = 0
    while sum(sizes) < num_envs:
        sizes[k - 1 - (i % k)] += 1
        i += 1
    while sum(sizes) > num_envs:
        j = max(range(k), key=lambda x: sizes[x])
        sizes[j] -= 1
    groups, start = [], 0
    for e, n in zip(entries, sizes):
        groups.append({"env_start": start, "env_stop": start + n, "seed": e["seed"], "fractions": e["fractions"],
                       "fraction_mean": round(sum(e["fractions"].values()) / len(e["fractions"]), 4), "layout": e["layout"]})
        start += n
    return groups


def mix_assignment(config: dict, support: dict) -> dict:
    """FootholdCfg.support_assignment for the continuous Tracker (task.py spawns each group's surfaces per env)."""
    groups = mix_groups(support["terrain_mix"], int(config["num_envs"]))
    return {"schema_version": 2, "kind": "terrain_mix", "num_envs": int(config["num_envs"]), "replicate_physics": False, "copy_from_source": True,
            "collision_filter": "explicit_environment_groups_with_global_ground", "calibration": copy.deepcopy(support["calibration"]),
            "matched_material": True, "groups": groups}


def mix_scene_spacing(groups: list[dict]) -> float:
    from parkour.shared_terrain import shared_scene_spacing

    return max(shared_scene_spacing(g["layout"]) for g in groups)


def describe_mix(groups: list[dict]) -> str:
    return "\n".join(f"group {i:2d} envs {g['env_start']:5d}-{g['env_stop']:5d} seed {g['seed']} f={g['fraction_mean']:.3f} len={g['layout']['nominal_path_length_m']:.1f}m"
                     for i, g in enumerate(groups))
