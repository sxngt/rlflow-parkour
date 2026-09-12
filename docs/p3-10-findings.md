# P3-10: map boundary removes artificial fourth-hop termination

| Fixed policy | Seed | P3-09 legacy radius | P3-10 map envelope |
|---|---:|---:|---:|
| mapped | 1 | 62/64 | 62/64 |
| mapped | 2 | 0/64 | 64/64 |
| strict | 1 | 0/64 | 0/64 |
| strict | 2 | 0/64 | 61/64 |

All four evaluation jobs and chained audits completed successfully. Root XY, root Z, foot positions and actions match exactly at every mutually valid recorded sample between old/new evaluations (p3-10-prefix-audit.json). This supports the termination-boundary explanation for the seed 2 difference; the policies were not retrained.

Both mapped-trained seeds now complete most/all of this 4-hop course under mapped_contact_v1 + map_envelope_v1. Seed 1 still has two failures; strict-trained seed 1 still fails before completing the first hop. These are 64 development scenarios per seed, not 64 independent trained policies. No champion promotion: previous basic-task regressions and broader terrain generalization remain unresolved.

Detailed raw results: p3-10-results.json. Videos and manifests are in result/*p3-10*. P3-11 extends the frozen mapped policies to 6/8 hops.
