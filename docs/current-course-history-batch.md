# Current autonomous research batch

User: continue until the final parkour objective or explicit stop. Do not finish the turn merely on launch or one small phase. Read actual process/supervisor/artifact state before repeating jobs.

Active command: `python3 scripts/research_course_history_batch.py > artifacts/course-history-batch.log 2>&1`
Exec session21031, started after source commitf6c9192. Six training jobs (all800updates/1024env): P3-15 longer jump seeds1/2; P4-03 history and zero control seeds1/2. Same-seed P3-08 mapped source checkpoint800. Global new-step budget117,964,800. Four workers own GPU indices only through run_job UUID leases. Training priority; completed jobs enqueue their common evaluations, so free workers backfill evaluations while other training continues. Plan: artifacts/course-history-batch-plan.json. Completed/failed state: artifacts/course-history-batch-state.json. This finite batch runner is not a complete resource broker or an unbounded autonomous service.

Each train includes native evaluation+64-robot video. Then P3-15 has4 common evaluations (reach and continuous for2seeds); P4-03 has16 (uniform8,friction0p2,friction0p05,continuous for4models). Total26 queued tasks plus6 native evaluations inside train wrappers. Reports scripts/p3_15_report.py and p4_03_report.py run only after all26 tasks succeed. Failure stops new admission but lets already executing jobs finish; artifacts are never overwritten. Investigate/recover missing tasks rather than rerunning successful training. State is persistent evidence, not automatic process resume.

Completed prerequisites: history clock/reset/mask/shared-normalization/initial-mean equivalence tests3; legacy fork tests4; history64env12update smoke and2update resume with native videos; longer-distance64env12update smoke/native video. Main training is not yet evaluated.

Research status:
- P3-11 uniform8 hops/1.2m foot goal: mapped seed1=48/64 seed2=64/64.
- P3-12 small alternating14.5/15.5cm: seed1=53/46,seed2=64/64 by pattern.
- P3-13 opt-in1cm elevation: upseed1=34/64,upseed2=15/64,downseed2=60/64. All-zero seed2 exactly matches old episode records/all existing200Hz trace channels. Actual first/last clone bounds and target-Z/landing-height errors audited.
- P3-14 strict airborne reach: bothseeds15cm16/16;20/25/30cm each0/16. P3-15 broadens training15–30cm on a wide deck, not physical-gap success.
- P4-02 alltraining/eval/report completed. Low-friction/control effects depend on seed and friction; regression remains. No champion. See p4-02-comparison.md and findings.
- P4-03 compares140ms history against zero additional inputs at identical535-input architecture. Shared66-channel normalization; seven validity bits; no contact-free/sensor-only claim. Current observation still contains oracle body state and contact-derived phase.

Geometry next: a simultaneous four-foot transfer between two whole-body platforms needs translation greater than calibrated front/rear footprint span+departure/landing margins. Measured span0.3735075m; with2cm margins a positive gap needs >0.4135075m. A50cm translation permits about8.65cm physical gap under this simple layout. Thus30cm reach training is a capability stage, not already a whole-body gap demonstration. Do not relabel per-foot pad gaps as that result.

Monitor18710 active, pagination verified and course completion panel deployed. New stages use phase:P3/P4 and explicit step tags. Keep64-robot camera_side4 overview plus supplementary individual closeups when useful, all in result with detailed titles. Continue to actual terrain/capability progression after this batch instead of waiting for every minor regression to disappear.
