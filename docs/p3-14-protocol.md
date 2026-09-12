# P3-14: airborne reach beyond 15cm

Frozen P3-08 mapped seeds1/2, wide existing deck, explicit one-hop legacy strict-travel contract. Evaluate15/20/25/30cm goals,16 development cases each per seed (64 per run). No new training. This measures commanded airborne translation/first-touch/stabilization on continuous support, not successful crossing of a physical gap. Parent policies were trained at15cm; larger distances are out-of-training commands. Shared deck bounds must contain each footprint before simulation.

Use the same3cm launch radius and goal−3cm minimum airborne travel, no altered rewards or motion limits. Preserve all failures and distance-specific criteria; do not pool the64 cases as64 independent trained policies. 64-robot camera-side4 MP4 and200Hz diagnostics. Run on currently free GPUs1/2 while history smoke usesGPU0. Results inform the next larger-gap capability curriculum, not a blanket superiority claim for a policy.
