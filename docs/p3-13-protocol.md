# P3-13: level stance height variation pilot

Pending execution after current GPU work. Fixed P3-08 mapped checkpoints; no new training. Extend geometric planning to horizontal four-foot stances at a common height, with vertical transition bound3cm. No slope or body swept-volume/dynamic validation is claimed. Actual collider center/top and target foot XYZ change together. Launch flight rise/apex is relative to the departure station; final body-height error is relative to the landing station. This is launch_and_landing_surface_relative_v1, recorded separately from historical flat tasks.

8×15cm forward transitions. Four pilot evaluations: seed2 all-zero heights (compatibility control), seeds1/2 [0,0,1,1,0,0,1,1,0]cm, seed2 [0,0,-1,-1,0,0,-1,-1,0]cm. Material remains authored0.5. Map contact validates actual elevated surface height. Keep 64-robot camera-side4 MP4, 200Hz target-Z/root/foot traces, hash and event audits. Check actual target Z and landing-error calculations each segment. Compare all-zero height execution with P3-11 seed2 before interpreting elevated outcomes.

This is a modest height-change pilot, not stairs/slopes/high jumps. It proceeds alongside P4 research because the final objective needs geometry progression as well as contact adaptation. New height code is opt-in and must preserve flat-task behavior. No physics success is inferred from geometry unit tests.
