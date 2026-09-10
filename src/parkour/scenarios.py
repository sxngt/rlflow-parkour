"""Versioned development scenarios. No final test set has been opened."""
from __future__ import annotations
import random


def development_scenarios(count=64, offset_m=0.06):
    if count < 1 or count > 1000 or offset_m < 0:
        raise ValueError("Invalid development scenario request")
    episodes = []
    for index in range(count):
        seed = 10000 + index
        rng = random.Random(seed)
        episodes.append({"id": f"t0-dev-{seed}", "seed": seed,
                         "foot_offsets_xy_m": [[rng.uniform(-offset_m, offset_m) for _ in range(2)] for _ in range(4)]})
    return {"schema_version": 1, "split": "development", "task": "a1_t0_foothold_v1",
            "target_offset_m": offset_m, "episodes": episodes}
