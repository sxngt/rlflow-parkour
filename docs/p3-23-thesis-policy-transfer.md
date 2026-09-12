# P3-23 — Existing walking prior from the user's thesis

Repeated cold-start continuous-target pilots remain stationary. Before spending further full-course PPO budgets on learning to move, check the existing A1 rough-ground PPO policy in the user-provided master-thesis project as a possible locomotion prior.

The selected rough-terrain seed2 best.pt, its resolved config, network code and Isaac Lab backend source were copied into artifacts/pretrained/master-thesis-a1-rough-seed2 with matching SHA256 hashes and provenance.json. The source directory has no Git metadata; no historical training commit is claimed. Actor weights are finite; architecture48→512→256→128→12, ELU. This is reused prior work, not a new parkour result.

Source observation is48 channels with fixed velocity scales and a forward-only body velocity command. Source action scale .25 maps to current .5 via a factor .5; previous action is converted back to source units. Current [-1,1] action clipping is retained and its fraction recorded. The common A1 asset supplies joint ordering and default pose. Current self-collision, terrain, force and failure contracts remain in effect, so this is transfer rather than an exact old-environment replay.

First test is a frozen-policy probe on the new easy ten-transfer course, source command1m/s (its original config target). The teacher consumes no foothold plan, maps or heading targets; it cannot be presented as the new Planner–Tracker. Any reached surfaces, actual displacement, jumps, failure and original follow video are diagnostic only. Only after observing useful walking should supervised policy initialization / adaptation be designed; no off-policy trajectories will be inserted into PPO updates.
