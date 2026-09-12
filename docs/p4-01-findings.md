# P4-01: contact-material sensitivity

| Fixed mapped policy seed | Uniform authored 0.5 | Later pads 0.2 | Later pads 0.05 |
|---|---:|---:|---:|
| 1 | 48/64 | 0/64 | 0/64 |
| 2 | 64/64 | 0/64 | 0/64 |

Resolved USD material assertions and all six chained audits passed (baseline plus four changed-material cases). With seed 2 and later-pad 0.05, all 64 cases finish three hops, touch down on the fourth with precise first-touch metrics, then time out. 59 show legacy precise stabilization at some point but none meets the mapped-contact gate at termination; joint contact/position timing needs examination. At 0.2, seed 2 splits between fourth-hop timeout and subsequent failure, including nonfoot collisions. These are diagnostic associations, not a unique slip cause.

Detailed segment exposure and supported foot-center motion (not proven slip) are in p4-01-comparison.json. Authored pad friction differs from effective robot-pad friction under average combine mode. No network weights were updated in P4-01.

Initial output names containing decimal points collided in supervisor log naming. Actual initial completions were seed1/0.2 and seed2/0.05; other requests failed before simulation. Preserve these records. Authoritative comparison uses seed1 friction0.2, seed2 friction0p2, and both friction0p05 attempts. The repeated seed2/0.05 result is not an extra independent replicate. Future names use p in numeric tokens. P4-02 compares explicit spatial-friction training with an equal-budget 0.5 continuation control.

Standalone diagnostic figures are exported to artifacts/p4-01-analysis/ by scripts/p4_01_plot.py. In the representative seed2/scenario20000 fourth hop, normal-material error settles below the5cm legacy radius; changed-material traces drift to roughly5.2cm while maintaining foot force. This illustrates why precise first touch alone is insufficient. It is one descriptive episode, not a confidence interval or a proof that every failure shares the same cause.
