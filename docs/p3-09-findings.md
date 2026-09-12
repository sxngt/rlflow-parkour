# P3-09: four-hop evaluation and legacy boundary confound

Fixed P3-08 checkpoints; 64 development initial conditions per model; no new training.

| Training condition | Seed | Four-hop successes | Completed-hop histogram |
|---|---:|---:|---|
| mapped | 1 | 62/64 | 3:2, 4:62 |
| mapped | 2 | 0/64 | 3:64 |
| strict | 1 | 0/64 | 0:64 |
| strict | 2 | 0/64 | 0:3, 3:61 |

All four process and chained artifact audits passed. Success uses mapped_contact_v1, not legacy strict trunk-flight distance. Four fixed 15cm foothold translations on 20 horizontal pads are not general high-speed parkour.

A concrete environmental limit invalidates interpreting the seed 2 fourth-hop failures solely as policy failures: JumpEnv retains the original root XY radius >0.6m termination. All 64 mapped seed 2 failures ended at radius 0.60026–0.61122m; all 61 strict seed 2 failures at 0.60023–0.60768m. The course goal itself is 0.60m. Mapped seed 1's two failures ended around 0.485–0.490m, so this boundary does not explain every failure.

P3-10 explicitly changes only the root outer boundary to the map surface XY envelope expanded by 0.20m, recording map_envelope_v1 and numeric bounds in the chain contract. Existing collision, fall, launch, first-contact and stabilization gates remain. Old results are retained. Full raw results: p3-09-results.json; artifacts/p3-09-*; detailed 64-robot evaluation videos in result.
