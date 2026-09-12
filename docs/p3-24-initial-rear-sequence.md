# P3-24 — Correct initial rear-foot target sequencing

P3-19/20/21/22 did not progress through the first surface. The old startup contract held rear targets at their own calibrated starting feet (-.258m X) while front targets moved to the first new surface (~.46m). After front acceptance, the rear target jumped directly to that surface, approximately .72m away. This also made initial body-waypoint shaping aim only ~.14m ahead and rewarded pinning the hind feet to the old stance.

The new opt-in `initial_rear_target=front_stance` makes the first rear targets the front feet's actual starting positions (~.114m X), before following the later shared surfaces. Front accepted index starts at0; rear accepted index starts at-1 because it has not yet occupied the first rear target. Rear index0 must be physically accepted and cannot advance to1 before front index1 is accepted. Intermediate target advancement never resets robot state or stops its velocity.

This is a changed target contract, preserving old `own_stance` runs and their checkpoints. It is a plausible structural explanation for the earlier stagnation, not a proved sole cause. Same ten-transfer easy map,105 observations, reward, precision curriculum, exploration and seed as P3-22. Initial budget800updates×1024env; strict native64episode evaluation and single-robot follow video. Only extend if measurable target progression develops.

Unit checks cover the rear pending index, first rear target matching the known previous front contact, progression ordering and reset, plus ray/slab target visibility. Before main training,12update64env smoke and native trace audit must pass. `completed_surface_transfers` is clamped at zero at startup; negative rear index is an explicit pending-start state, not negative movement.
