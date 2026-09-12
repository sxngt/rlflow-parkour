# P3-10: map-derived root boundary

Repeat P3-09's four fixed policies and 64 development scenarios with identical 4-hop geometry, geometric planner, mapped_contact_v1 and 4s/hop budget. Change only the root XY outer bound from the legacy 0.60m radius to map surface envelope +0.20m per side. Record version and numeric bounds in run/scenario/evaluation chain contracts. This is an explicit environment contract change, not a correction to historical scores.

No new training. Run through UUID leases, 64-robot camera-side 4 MP4, 200Hz trace and chain audit. Compare event prefixes before old boundary termination, new full-course success, remaining launch/contact failures. Do not claim new robustness from repeated deterministic development cases.

The next independent extension is 6/8-hop geometry (90cm/120cm goals); it requires expanded runtime horizon support and explicit map boundary, rather than applying the old radius to longer courses. Final research still needs nonuniform terrain, turns, slopes and dynamic planning.
