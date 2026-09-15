<h1 align="center">rlflow-parkour</h1>
<p align="center"><b>A Unitree A1 quadruped crosses a parkour course of 24 separated pads in consecutive jumps.<br>A reinforcement-learning curriculum took the course from 25% to 92% difficulty.</b><br>
Isaac Sim 4.5 · Isaac Lab 2.1.1 · PPO (rsl_rl) · Ray Tune · <a href="https://github.com/sxngt/rl-flow">RLflow</a></p>

<p align="center"><img src="docs/media/hero.gif" width="720" alt="24-gap parkour course, showcase A"></p>
<p align="center"><sub>Showcase A. Gap 89% · turn 92% · tilt 86% · height 92% · size 95%; 57 of 64 episodes completed. Red dots are the four-step footfall plan drawn on the pads, the large one being the predicted next landing.</sub></p>

---

## Results

| | Map difficulty (gap / turn / tilt / height / size) | Completed (64 ep) | Policy |
|---|---|---|---|
| **Showcase A** | .89 / .92 / .86 / .92 / .95 | **57 / 64 (89%)** | `parkour/v51` |
| Showcase B | .89 / .92 / .86 / .95 / .98 | 48 / 64 (75%) | trial `e3c085b6` |
| Showcase C | uniform .86 | 56 / 64 (88%) | `parkour/v45` |
| Starting point | uniform .25 | 57 / 64 (89%) | `parkour/v5` |

The course is `mixed_discrete`, 24 gaps, geometry seed 1. Difficulty is set per axis as a fraction from 0 to 1 on gap length, turn angle, pad tilt, height change and pad size; at 100% the gaps reach 0.70 m, rises ±0.27 m, turns 50° and tilts 22°. Evaluation is deterministic with a frozen policy over 64 episodes. An episode counts as complete when all four feet stand on the last pad for 0.2 s. Any trunk contact with a pad ends it as a failure.

The 100% map is not solved. The best policy still falls at the fourth transfer. The numbers here stop there.

## How the difficulty went up

<p align="center"><img src="docs/media/curriculum.png" width="820" alt="curriculum progression"></p>

Each stage does the same thing. Fork the best checkpoint of the previous stage, train 1200 iterations on a slightly harder map, evaluate frozen. If at least 75% of the episodes complete, that policy becomes the parent of the next stage. If not, training continues on the same map; if completion is close to zero, the curriculum steps back. The first eighteen stages raised all five axes by the same amount. From 86% on, the axes moved separately, for reasons covered below.

<p align="center"><img src="docs/media/stage-outcomes.png" width="820" alt="stage outcomes"></p>

Every stage on a difficulty–completion plane falls into one of three groups: passed, below threshold and continued, or collapsed. The four collapses happened at 0.74, 0.81, 0.83 and 0.89, and at the time they looked like cliffs in the terrain.

<p align="center"><img src="docs/media/training-curves.png" width="820" alt="training curves per stage"></p>

Learning curves of the best trial per stage. The budget is the same everywhere, 2048 environments × 1200 iterations, about 5.9 × 10⁷ steps, and training converges inside it at every difficulty. Training EMA is measured on rollouts with exploration noise, so it sits below the frozen evaluation; the 71–79% stages, which still used a noise floor of 0.12, show this most. Every curve also has a flat stretch near zero for the first few million steps. That stretch is the trace of the fork problem.

## What we learned

### The collapses were caused by the fork learning rate, not the terrain

<p align="center"><img src="docs/media/fork-lr.png" width="640" alt="fork learning-rate A/B"></p>

A parent policy is saved with its learning rate driven down to about 1e-5 by rsl_rl's adaptive KL schedule. The child started a fresh Adam optimizer at the config value of 2e-4. The first PPO update then acts almost like sign descent on a mature policy: the robots are fine in the first rollout and start falling by the hundreds from the fifth iteration. Recovery took several million steps, and four times it never came.

An A/B on the same 86% policy forked onto the 0.89 map (1024 envs, 40 iterations) made the mechanism plain. With LR 2e-4 the mean number of transfers per episode dropped from 3 to 0.1 within twelve iterations; with 1.5e-5 it climbed from 7 to 13. Every fork since inherits the parent's final learning rate through `+fork_lr=inherit`.

### Raising all five axes at once creates a cliff

<p align="center"><img src="docs/media/cliff-vs-pass.gif" width="720" alt="uniform 0.89 fails, per-axis map passes"></p>
<p align="center"><img src="docs/media/probe-matrix.png" width="640" alt="per-axis probe matrix"></p>

Put the 86% policy on the uniform 0.89 map and all 64 episodes end at gap 13 (0.70 m across, 0.18 m up) with the trunk catching the landing pad. Raise a single axis to 0.89 instead and it completes 41 to 58 of them. One uniform step was five perturbations at once.

From here on, a frozen probe sits between stages. The current policy is evaluated for 30 s each on maps with one axis raised by 0.06 or 0.03, the combination of tolerated axes is probed again, and that combination becomes the next map. The matrix above is the probe of the 86% policy: height change and pad size have room, gap length has a wall between 0.89 and 0.93, and tilt is tight even at 0.89.

<p align="center"><img src="docs/media/axis-frontier.png" width="720" alt="per-axis frontier"></p>

With axes moving separately, the frontier advances at a different pace on each. Height and size reached 0.95 and 0.98 first, turn followed, tilt stayed at 0.86 and gap length stopped at 0.89. Those two axes are the next problem.

### Less exploration noise was better

<p align="center"><img src="docs/media/std-sweep.png" width="640" alt="exploration std sweep"></p>

The floor on the Gaussian noise added to policy outputs was swept over 0.04, 0.06 and 0.08 from the same parent. On the 86% map the training EMA came out at 0.72, 0.46 and 0.12, and 0.04 kept winning in later stages. When refining a mature policy, exact rollouts mattered more than the mistakes noise can generate.

### Mixed terrain prevents forgetting but does not push the frontier

`terrain_mix` assigns maps of different difficulty to different environments and trains on all of them at once. Performance on the easier maps held, but at difficulties the policy could not yet handle there was no success signal to learn from, and the frontier stayed put. It did not replace the curriculum; it stays as a supporting tool.

## Footfall plan overlay

<p align="center"><img src="docs/media/footfall-plan.gif" width="560" alt="4-step footfall plan overlay"></p>

The policy is an MLP from a 105-dimensional observation to 12 joint targets; it does not output footsteps. The video therefore draws an estimate. The large dots are the next landing prediction: time-to-pad from the current body velocity, plus the nominal stance offset of each foot, snapped onto the pad surface. The three smaller steps are the pair targets the planner fixed per pad. When a foot lands, the plan advances one pad. Display only; it plays no part in reward or scoring (`src/parkour/predicted_footfall.py`).

## Method in brief

```
[map]     curriculum_maps.build_mixed_discrete_axes(seed, {gap, turn, tilt, height, size})
[train]   PPO (rsl_rl), 105-dim obs → 12 joint targets, 2048 envs × 1200 iters
          fork = best checkpoint of the previous stage + fork_lr=inherit + min_std 0.04
[sweep]   Ray Tune — exploration std, learning-rate multiplier, candidate maps
[eval]    frozen policy, 64 episodes → gate native ≥ 0.75 → MLflow registry candidate → validated
[next]    frozen probes (per axis +0.06 / +0.03, then combinations) → next map
```

- Policy, terrain, evaluation, recording: `src/parkour/` (`continuous_tracker_task.py`, `curriculum_maps.py`, `policy_fork.py`, `terrain_mix.py`, `predicted_footfall.py`, `media.py`)
- RLflow entry points: `train.py`, `evaluate.py`, `export.py`. Configs in `configs/*.yaml`, sweeps in `configs/sweep/`, evaluation suites in `eval_suite/`
- Curriculum driver: [`rl-flow/tools/parkour_campaign.py`](https://github.com/sxngt/rl-flow/blob/main/tools/parkour_campaign.py) — `stage` / `auto` / `auto-axes` / `auto-multi`
- How to run: [docs/rlflow-usage.md](docs/rlflow-usage.md). Research notes (490 files, Korean): [docs/](docs/), handover in [active-research.md](docs/active-research.md). Pre-migration README: [docs/legacy-readme.md](docs/legacy-readme.md)

## Scale

| | |
|---|---|
| Curriculum | 50 stages, 51 sweeps, about 150 trials |
| Training | about 5.9 × 10⁷ environment steps per stage, about 9 × 10⁹ in total |
| Evaluation | frozen 64-episode evaluation at every stage, 55 policy versions registered |
| Assets | 1,456 runs (1,378 migrated + 78 new), 900+ videos |

Runs, metrics, videos and lineage live in the RLflow console under `/p/parkour` and in MLflow. The three showcase runs carry the tag `purpose:showcase`.

## Background

The original research (`workspace/parkour`, 351 commits) built a prior-map Planner–RL Tracker in stages: single jump, chained jumps, mixed terrain. In September 2026 it moved into an RLflow project; 1,375 runs and 900 videos were imported without touching the source, and all training and evaluation since then goes through RLflow. The implementation was done together with an AI coding agent (Claude Code).
