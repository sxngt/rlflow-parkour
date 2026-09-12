# Research continuation handoff: P3 course extension → P4 contact conditions

User explicitly requires ongoing autonomous progress until stopped, not a final response after a small step or launch. Preserve this objective. No permission needed for owned four GPUs; use run_job leases. No sub-agent authorization.

Completed this continuation:
- P3-09 four-hop evaluation exposed old root-radius 0.60m termination at a 0.60m goal.
- P3-10 explicit map_envelope_v1: mapped seeds 1/2 four-hop 62/64 and 64/64. Common valid trace prefixes exactly equal old execution.
- P3-11 six/eight hops: seed1 54/64 and 48/64; seed2 64/64 both. Supplementary single-robot closeup preserves all 64 episode results/200Hz traces exactly and is archived alongside 64-robot overview.
- P3-12 alternating14.5/15.5cm eight-hop: seed1 53/64 or46/64 by order; seed2 64/64 both. Initial summary failure retained; authoritative retry1 results validate per-segment goal distance. Runtime planner/commands now use actual nonuniform offsets.
- P4-01 later pads authored friction0.2/0.05: both seeds0/64 full eight-hop. Runtime USD material checks pass. See p4-01-comparison.json for segment exposure/diagnostics. Initial decimal filename collisions retained; authoritative paths documented in p4-01-findings.md.

Current P4-02 main pipeline:
`python3 scripts/p4_02_pipeline.py > artifacts/p4-02-pipeline.log 2>&1`
Initial exec session88841. Check actual processes/supervisors before restarting. Four runs lowfriction/control × seeds1/2; source same-seed P3-08 mapped checkpoint800. 1024env×24×800 each. Training3hop, stations2/3 authored friction0.2 vs0.5 control, no observation/reward change, fresh optimizer fork. Smoke12 and resume2 succeeded including native64-robot videos/artifact gates. Tests cover changed terrain cannot resume, invalid material schedules, legacy fork contracts and nonuniform summary/map.

Pipeline stages: four training/native evaluations →16 matched evaluations (uniform8, friction0p2, friction0p05, continuous0/5/10/15cm permodel) → report. `--start-at evaluate|report` avoids repeating completed training if postprocessing fails. Each stage checks prerequisites and refuses to overwrite attempts. Continue interpreting results and implementing next research work after this stage; do not end merely because pipeline launched.

Limits: horizontal small-pad stabilize-then-jump, not high-speed varied 3D parkour. Planner is geometric, no physics-rollout yet. Current66obs includes oracle body state and four contact bits; no history encoder yet. Friction numbers are authored pad values with average combine, not measured effective contact coefficient. Keep previous continuous-regression losses visible; no automatic champion promotion.
