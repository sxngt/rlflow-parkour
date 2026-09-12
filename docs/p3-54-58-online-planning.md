# P3-54–58: airborne cloning, medium retraining and asynchronous planning

Development experiments, 2026-09-13. No final-test or champion claim.

P351 24-gap easy frozen evaluation completed 58/64 on identical geometry clones. Fixed first robot succeeded in 11.26s, travel10.38s, five strict ≥3cm-body-rise jumps. P353 capped-progress/speed-cost package completed60/64 versus64/64 matched control; fixed first travel7.20s versus6.16s. These are development comparisons, not independent terrain generalization.

P354 cloned clean airborne root/joint/controller state, preserving pending targets and policy hash. Articulation readback error≤12μm and initial0.2s baseline root prediction errors<0.1mm. Hidden PhysX solver state is not stored. Removing reward/flight accounting only in the frozen planner reduced a matched72-branch assay from2.8s to1.7s, with identical recorded outcomes/short predictions. Full actor observations, motor limits, contact/progress/failure gates remain enabled.

P355 compared1200updates×1024env with/without a parabolic gap body-height reference (apex0.12m,cost80). Both failed after four medium transfers,0/64. Artifact audits passed. This reward alone did not solve the bottleneck. P356 now compares explicit exploration caps0.30→0.20→0.12 against0.12 throughout, same parentP355control1200 and learning rate0.0001,1200updates each. Intermediate noisy-rollout performance is not frozen policy evaluation.

P357 uses persistent workers on separate UUID-leased GPUs and atomic local file mailboxes. The executor advances at50Hz target frequency while a hot9-env planner predicts committed motion, branches four future surface goals, and sends a scheduled proposal. Candidate4 preserves already committed goals; other candidates are nominal map goals±8cm longitudinal/±4cm lateral. This is goal-position planning on a fixed surface route, not route discovery. Cold airborne snapshots are bound to exact policy/environment contracts. The current landing remains unchanged. Expired proposals, contact-index disagreement or predicted root error>8cm are rejected.

- First integration completed24gaps but applied no proposals: first deadline miss plus inference-tensor restore errors. Preserved as failed integration evidence.
- R2 fixed inference context:4/5 responses applied but all retained the old plan. Warm planning~1.1s, first1.60s missed1.5s deadline.
- R3 prewarmed the worker and moved durable request writes off the control thread. All5responses arrived before scheduled activation; one changed future goal positions. Execution succeeded24/24 in11.24sim seconds,10.42travel seconds, six instrumented strict jumps. Wall11.40s. No original-camera claim: separate recorded-state playback is rendered afterward.
- R3 still exceeded20ms compute on98/562ticks, max170ms. This is NOT verified real-time control. Planning predicted1.5s committed prefix and only0.3s physical branch, so it is NOT four-step physical completion validation.

P358 extends branch simulation until both contact pairs reach the fourth proposed surface (or failure/budget), records horizon outcomes and tests one CPU intra-op thread. Scheduled lead is increased explicitly for the latency assay; physics/control dt are unchanged. Results must establish whether this longer validation arrives in time. No performance improvement inferred from a changed target alone.

All source snapshots and failed attempts are retained. Online pilot scores integrate speed tracking error and a small action magnitude cost; they are not the final RQ1 metric. Required next evidence: full physical horizon responses, paired fixed-plan evaluations on varied maps, candidate diversity/replicas, control deadline improvement, and medium-course completion. Dynamic surface choice and event-driven adaptation remain unfinished.


P358 outcomes: 3s scheduled lead gave3.35/3.31s physical planning and both proposals correctly missed deadline. All nine candidates reached the fourth surface. With explicit4.5s lead, one full-horizon candidate6 was applied after4.26s planning; activation position prediction error0.865mm. The robot completed24gaps,10.42s travel, five strict jumps. A second proposal was rejected near the terminal because four intermediate surfaces no longer existed. This establishes a functional long-latency physical planning path, NOT fast reactive replanning.

P359 diagnosis: actor mean absolute value>0.98 on16.2% of medium outputs versus29.5% easy. Saturation exists but is not unique to the failing medium policy; this evidence does not justify attributing failure solely to tanh saturation. No actor reset was adopted.

P360: two24-gap harder terrain configs and12-update calibration smokes. Direct full medium gap0.35m/tilt12deg/height amplitude0.18m/turn22deg; explicit halfway curriculum gap0.265m/tilt9.5deg/height0.14m/turn17deg. Every full cuboid remains separated. Both fork P351easy1200 with LR0.0001,1200update budgets. Existing easy/medium/hard v1/v2 geometries are unchanged. Blended geometry gets its own canonical contract; benchmark override deliberately generates full requested difficulty.
