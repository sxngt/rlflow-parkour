# P3-12: small nonuniform spacing transfer

Eight hops, alternating 14.5/15.5cm, same 1.20m goal. Fixed mapped P3-08 checkpoints:

| Seed | Uniform 15cm (P3-11) | Short-first | Long-first |
|---|---:|---:|---:|
| 1 | 48/64 | 53/64 | 46/64 |
| 2 | 64/64 | 64/64 | 64/64 |

Initial attempts failed during summary generation after physics execution because the old single-distance grouping equated first and last hop distances. Those attempts and logs are retained. Retry1 fixes this contract: every executed hop's goal is checked against its segment's distance, and results are summarized by whole course. All four retry1 jobs, artifact collection and chained audits passed. No new training. Small spacing variation transfers for seed 2; seed 1 remains less reliable. This is two deterministic geometric patterns, not broad random terrain robustness.

Authoritative results: p3-12-retry1-results.json; artifacts/result names end in retry1. Failed-attempt summary p3-12-results.json is not a policy performance result. The planner reads actual surface geometry; per-hop absolute targets and distances are stored in chain_contract/chain-events/geometric-plan.
