# P4 observation audit before contact/history ablations

The current directed-jump policy receives 66 scalars. This is a simulation baseline, not the final sensor-only deployment contract. Source: FootholdEnv._get_observations and JumpEnv._get_observations.

| Slice (zero-based, end exclusive) | Content | Current origin |
|---|---|---|
| 0:3 | Body-frame linear velocity | Simulator rigid-body state |
| 3:6 | Body-frame angular velocity | Simulator rigid-body state |
| 6:9 | Projected gravity | Simulator orientation |
| 9:21 | Joint position minus default | Simulator joint state |
| 21:33 | Joint velocity ×0.05 | Simulator joint state |
| 33:45 | Applied previous control-step offset command | Controller state |
| 45:57 | Four next-foot targets, body-relative XYZ | Map target plus exact body pose |
| 57:61 | Four contact bits | Net foot-force hysteresis, onset5N/release2N |
| 61:64 | Preparation/flight/landed one-hot phase | Task state derived from force-history flight and contact onset |
| 64:65 | Required apex minus current root rise | Exact simulator height and calibrated starting root height |
| 65:66 | Preparation clock clamped at1 | Local maneuver time |

The phase channel also carries contact-derived information. Zeroing only the four contact bits is therefore not a clean no-contact B0 ablation. It would be a limited sensitivity probe, not RQ2 evidence. Current actor and critic use the same normalized observation; no teacher/student separation has been implemented. The initial policy sees no explicit friction coefficient or future contact force, but exact body pose/velocity and ground-truth-derived task phase remain oracle information.

P4-01/02 vary physical pad materials while preserving all observation fields. They establish sensitivity/continued-learning baselines only. Before a B0/B1/B2/B3 comparison, define a versioned common reference-command phase independent of measured contact, remove or sensor-model the true-height term, specify linear-velocity estimation/error, and route contact bits/phase through one sensor provider with timestamps, masks and reset behavior. Append history only after the per-step contract is fixed; account for network parameter/computation changes and train all variants under matched budgets. Do not label old checkpoints as sensor-only or no-contact policies retroactively.

The final terrain objective still requires vertical target heights/slopes/turns and dynamics-aware candidate validation. Current geometry planner handles horizontal translated stances and is not a completed RQ1 rollout planner.
