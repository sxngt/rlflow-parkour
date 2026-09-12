# P3-15: train a broader airborne reach envelope

Capability-extension pilot after P3-14's0/16 success at each20/25/30cm command. Two seeds1/2 start from same-seed P3-08 mapped checkpoints, new optimizer/RNG. Train one-hop on the existing wide deck with uniformly sampled15–30cm commands. Preserve robot, observation66, PPO, reward terms,3cm launch radius and goal−3cm airborne body-travel gate. The minimum required apex remains unchanged and is not an upper height bound. Remove the chain adapter explicitly; episode length4s. This is a new single-hop training task, not resume or physical-gap completion.

Each main run1024env×24×800=19,660,800 steps; total39,321,600. Two seeds constitute a capability pilot without an equal-budget15cm control, so do not claim causal superiority of this curriculum. Check endpoint footprint containment before training. Require64env12-update smoke and source-fork validation, finite learning metrics/checkpoint and native64-robot evaluation.

Final fixed comparison uses15/20/25/30cm (16 cases each), legacy strict-travel single-hop deck, plus continuous0/5/10/15cm regression. Keep64-robot camera-side4 MP4,200Hz diagnostics, detailed result titles and phase:P3 tags. A successful deck jump still needs subsequent physical gap validation. No reward or success-threshold relaxation to make larger distances appear successful.

Schedule these two jobs alongside the four P4-03 history/control jobs using a shared bounded six-job queue; GPU workers take the next job after previous train/native evaluation releases its lease. Both P4-03 arms retain the full equal800-update budget.
