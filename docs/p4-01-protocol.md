# P4-01: spatial friction sensitivity baseline

Begin contact-adaptation phase with fixed P3-08 mapped policies, seeds 1/2. Use the P3-11 uniform 8-hop/1.20m course. Keep pad materials at authored static/dynamic friction 0.5 through station 3; stations 4–8 use either 0.2 or 0.05. Four evaluations, 64 development cases each, no new training. Geometry, plan, observation, controller and success gates stay fixed. Robot material is unchanged, combine mode remains average: these numbers describe pad material, not a measured effective contact coefficient.

The evaluator records per-surface overrides and spatial_friction_v1. Inspect resolved USD collider material bindings in first/last environments and assert each changed support has the requested coefficients; save collision-contract.json. Keep 64-robot camera-side 4 MP4, 200Hz trace and chained audits. Compare complete-course and segment results to P3-11. Measure slip from supported-foot motion as a diagnostic; do not infer a unique physical cause from a fall alone.

This is the contact-bit baseline's sensitivity characterization, not yet an RQ2 contact/history ablation or a trained adaptive policy. Current policy includes oracle body state and four contact bits. New sensor/history variants need explicit observation contracts and matched training budgets.
