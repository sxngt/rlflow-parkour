"""Versioned development scenarios. No final test set has been opened."""
from __future__ import annotations
import random


def development_scenarios(count=64, offset_m=0.06, sequence=None):
    if count < 1 or count > 1000 or offset_m < 0:
        raise ValueError("Invalid development scenario request")
    episodes = []
    for index in range(count):
        seed = 10000 + index
        rng = random.Random(seed)
        offsets = ([[rng.uniform(*sequence['forward_step_range_m']), rng.uniform(-sequence['lateral_step_m'], sequence['lateral_step_m'])] for _ in range(4)]
                   if sequence else [[rng.uniform(-offset_m, offset_m) for _ in range(2)] for _ in range(4)])
        episodes.append({"id": f"{'t0s' if sequence else 't0'}-dev-{seed}", "seed": seed,
                         "foot_offsets_xy_m": offsets})
    if sequence and sequence.get('randomize_first_foot',False):
        names=['FL_foot','FR_foot','RL_foot','RR_foot']
        for index,episode in enumerate(episodes):
            order=[(index+j)%4 for j in range(4)]
            episode['episode_order_indices']=order
            episode['active_foot']=names[order[0]]
    return {"schema_version": 1, "split": "development", "task": "a1_t0_sequential_v2" if sequence else "a1_t0_foothold_v1",
            "target_offset_m": offset_m, "episodes": episodes}
