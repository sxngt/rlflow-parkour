# P3-11: sustained horizontal course execution

Frozen P3-08 mapped policies, map_envelope_v1 and mapped_contact_v1, 64 development cases each:

| Seed | Six hops / 0.90m target | Eight hops / 1.20m target |
|---|---:|---:|
| 1 | 54/64 | 48/64 |
| 2 | 64/64 | 64/64 |

All jobs and chained audits passed. No extra training. This establishes sustained stabilize-then-jump execution on the measured horizontal fixed-spacing course for these checkpoints. It does not establish high speed, arbitrary gaps, slopes or turns. Seed 1 degrades with length; seed 2 remains the stronger course candidate but previous regression findings still apply.

Each evaluation retains 64-robot camera-side 4 video and 200Hz traces; completed-hop distributions and event audits: p3-11-results.json. Next: P3-12 changes spacing to alternating 14.5/15.5cm (both phase orders), preserving the 1.20m eight-hop goal.
