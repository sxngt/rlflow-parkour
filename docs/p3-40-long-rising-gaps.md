# P3-40 — Integrated long rising-gap scenarios

User target: long difficulty-based dynamic routes and single-robot third-person follow recordings. P339 now records12.5s actual travel over60transfers/10gaps, but0/64terminal success and0strict3cm-risejumps. Low running bounds are real airborne events; they are reported separately and not renamed large jumps.

New long_ten_gap_course_v3 raises terrain by5cm or10cm at each gap, keeping the original first approach unchanged. Ten rises total0.5/1m; intermediate approaches remain on each new level. Defaultv1/v2 geometry stays identical. Exact constructor, target exposure and height-difference tests pass.

40transfer geometry-onlysmokes: rise05 reaches25.81transfers;rise10reaches3;0strictjumps. No main40runs. Integrated60transfer configurations combine56.25cm nominalgaps, fiveapproaches per gap, landingbodyreference, gapflightcredit10, terminalmotioncost2. These are integrated engineering scenarios, not an isolated multi-factor causal comparison. Both12×64smokes passed physics/trace audits and reachfirstgap5/60. Main1600×1024 per height, parentP338gap125bonus800, parentadaptiveLR2.25e-5 andstdcap.12 retained. GPU0rise05session68626/GPU1rise10session7449. Evaluate frozen finalcheckpoint and original fixedenv0follow video; no final performance promise.

Metric change: clean airborne count can include terminal rocking. New travel_clean_airborne_count and travel_measured_jump_count exclude landings after both targets enter finalstance. Demo eligibilityv5 tightensv4 by requiring8strictjumps during travel itself, not jumps accumulated while waiting at the goal. Old artifact reports remain unchanged.
