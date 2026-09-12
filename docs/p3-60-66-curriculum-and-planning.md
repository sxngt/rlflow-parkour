# P3-60–66: harder long maps and physical-planning integration

Development work, 2026-09-13. No champion promotion, final test claim, or hardware deployment.

P360: 1200updates×1024env from the same P351easy1200 checkpoint. Halfway-to-medium24-gap curriculum (nominal full-box gap26.5cm, tilt9.5deg, height amplitude14cm, turn17deg) achieved36/64 native completions; mean23.546875/24 transfers. Direct full medium35cm achieved0/64, first robot4transfers. Curriculum checkpoint still0/64 when immediately evaluated on full medium. These evaluation and physics trace audits passed. This supports a staged progression, not full-medium success.

The fixed first curriculum robot reached all24surfaces then collided at the terminal; travel11.08s and eight strict travel jumps. Do not describe its original video as successful. Among complete episodes, env3 traveled11.02s with12strict jumps; env4 traveled11.00s with10. P365 predeclares env3 for a NEW64-env evaluation and follows it, with the prior-success selection disclosed. It does not reconstruct the old episode. All64 outcomes remain in the new report. The source evaluation remains unchanged.

P363 stage2 is running: curriculum26.5→30.75cm versus direct35→35cm,1200additionalupdates each, fresh optimizer both. Same initial P351 parent and cumulative environment-step budgets. Native videos and full35cm evaluations are queued. Advancement gate was mean≥16transfers, fixed before the P360 frozen evaluation; the observed23.55passed. Geometry is still one development seed and does not establish generalization.

P356 frozen exploration restart result:0/64 for both arms, exploration first robot5transfers/2strict jumps versus control4/3. This is modest progress beyond the old collision point, not medium completion. P362 restarts the same explicit exploration schedule from P356explore1200 in both arms, with/without stronger gap clearance apex20cm/cost200;1200updates each. P355 weaker apex12cm/cost80 previously had no effect. This is a new reward magnitude pilot, not an established improvement.

P361 collected one fixed Tracker on three new easy maps (seeds2,3,101), four airborne contexts per map, nine candidates with eight numerical replicas each.108candidate groups/12contexts,410successful and454failed four-surface rollouts, no censored outcomes. Episode/map groups and Tracker hash are preserved in artifacts/p3-61-r2-feasibility-dataset. These are correlated replicas, not864independent terrain tests. A missing diagnostics flag stopped the original collector; its completed video/evaluation remains as evidence. Retry filenames use r2 and include200Hz traces. Override-map airborne state hashes now bind the actual evaluated terrain instead of the training terrain; the resulting clone assays passed.

P364 CPU logistic pilot uses128translation/yaw-invariant body-frame features. Leave-one-map-out Brier0.5838 versus constant0.3969 (lower is better). Of440replicas belonging to candidate groups assigned probability≥0.8,310failed. The model is rejected for controller use. This is only three map groups; more diverse data and improved modeling are needed. No learned admission gate was installed. The final fit file is a diagnostic artifact, not a validated policy bundle.

P366 is queued after P362andP365 release GPUs1and3. It applies full-four-surface physical planning to P360's stronger26.5cm24-gap Tracker, compares a single fixed-plan episode on the same checkpoint/map, and renders separately captured states. The4.5s scheduling lead remains a latency limitation. Source/root/joint state playback is labeled distinctly from original camera frames. Completion and control deadlines must be read from the actual resulting reports.

Persistent drivers use UUID leases and finite budgets. P360andP362 drivers were adopted after correcting diagnostic/dependency handling; active training wrappers were preserved, not duplicated. Current driver PIDs are in the handoff document; run supervisors, not PIDs alone, determine success and resource release.

P365 video QA found a nonzero-clone visibility inheritance bug: hiding env0 also hid env3. The original empty-floor video is explicitly marked invalid in result/; its evaluation remains36/64. MakeVisible on the followed environment fixes the inherited attribute; a ComputeVisibility guard was added. R2 new evaluation again36/64, selectedenv3 succeeded in12.50s with11.02s travel/12strict travel jumps. Actual frame at5.5s verified robot/terrain visible. Mean/p95/max horizontal speed over that episode2.02/2.50/2.70m/s. This is original footage of the new evaluation, not a reconstruction of the previous success.

New physics diagnostics include root quaternion and world angular velocity for all evaluated robots, enabling future exact-state playback sources without another policy execution. Existing traces are not retroactively changed.

Online plan admission now additionally rejects predicted/current orientation disagreement>0.15rad, joint-position max error>0.15rad and velocity difference>0.5m/s. Historical position-only assays remain unchanged. Tests cover matching positions with wrong orientation.

Workers now resolve lazy parkour imports from their recorded source snapshot; preloaded package modules are listed. This prevents workspace edits during Isaac startup from changing later task/media imports. A subprocess import-path check passed; future simulator attempts validate the complete path.

P368 queued stage3 afterP363: both arms on full35cm24-gap terrain,1200additionalupdates each, same cumulative3x1200updates sinceP351. Advance only when the stage2 curriculum frozen mean≥16transfers. This remains development curriculum evidence, not an optimal curriculum claim.
