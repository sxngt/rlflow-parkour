## Active update — 2026-09-12 20:10 KST

- P3-19 seeds1/2 completed3000each, native0/64each, both audited/archived. P3-20 completed2400, native0/64. P3-21 completed600, native0/64; collection typo fixed and collection rerun. P3-22 completed800, native0/64, no extension. All earlier sessions finished.
- Frozen thesis priors tested: roughseed2 failed0.20s; flatseed3 moved~.28m thenfailed0.56s; expanding actionlimit1→4 removed clipping without helping; stairsseed1 failed0.24s trunk contact. These are not adopted as champions or pretraining. Archives/provenance under artifacts/pretrained; source has noGit metadata.
- New opt-in initial rear target=front_stance: rear first steps to the known initial front position; starts accepted index-1. Prevents holding rear at starting rear location then requesting~.72m first rear stride. Target scriptv2; oldown_stance defaults/checkpoints unchanged.
- GPU0: P3-24 both-foot corrected-start pilot, `artifacts/p3-24-rear-sequence-seed1-pilot800`, session75687,800updates1024env. Aroundupdate460 sparse front progress. Native evaluation follows automatically.
- GPU1: P3-25 either-foot corrected-start, `artifacts/p3-25-either-foot-seed1-pilot800`, session19123,800updates1024env. Front mean.02148 atupdate39, trainingradius.25; notstrictsuccess.
- GPU3: independentP3-25 seed2 `artifacts/p3-25-either-foot-seed2-pilot800` (latest exec session printed by launcher).800updates1024env, same settings. Evaluate before extension.
- GPU2: strict interimP3-24 checkpoint300 evaluation `artifacts/p3-24-rear-sequence-interim300`, session67901,16episodes+200Hz+singlefollow. Wait for release before further probes.
- P3-24/25 smoke+nativeaudits passed. Fixedstrict6cm evaluations, finalall4stabilization eveneitherintermediatequorum. Dynamicdemo requires10transfers,>=10actuals,>=8measuredjumps. No qualifying result yet. New diagnostics include body displacement/path length and nonfoot failure bodyIDs; pathlength includesoscillation.
- Latest source commit55bd3b2 plus thishandoff/doc update. Web rebuilt withdifficultyfilters andschema2diagnostics; actualbrowsersearch/detail/followtrace verified. Stay onthelongsharedmaps; donotreturntooldstraightpads.

## Latest execution update (2026-09-12 19:39 KST)

- P3-19 baseline seeds1/2 still active on GPUs0/1 (session48387), roughly1700/3000 updates, no first-surface progress. Checkpoint500 native easy diagnostic:0/16, all30s timeout,0jumps. Corrected-config retry completed. Held-out medium geometryseed101 evaluation and 200Hz audit completed0/16, with follow video. All archived in result.
- GPU3 P3-20 `artifacts/p3-20-long-contact-seed1`, session46250,2400updates,1024env. Curriculum tolerance .25→.18→.12→.08→.06 and stdfloor.12. Still zero progression nearupdate600. Smoke and explicit resume12→14 + native evaluation audits passed. Evaluation always strict6cm.
- GPU2 P3-21 `artifacts/p3-21-long-body-seed1-pilot600`, session46482,600updates first budget,1024env. Only extra reward relative to P3-20 is within-step progress toward current body waypoint. Smoke+nativephysicsaudit passed. Do not extend a zero-progress result; inspect completion first. Config contains full2400schedule for possible later continuation.
- All4 GPUs currently leased by owned training jobs. Do not collide with native final evaluation stages. Medium/hard geometry previews copied to result/previews with explicit no-policy labels.
- Latest commit ce513cc. Web built and backend health verified18710; continuous diagnostics no longer crashes old frontend, new follow traces include feet/forces/actions/indices. Final demo eligibility dynamic_long_course_v2 requires10transfers,>=10actuals,>=8measuredjumps,successfulcourse; no qualifying result yet.

# Active handoff — P3-19 long scenarios (2026-09-12)

Latest user requirement supersedes parallel final videos: difficulty-tiered long courses, about ten dynamic movements and over ten seconds of actual successful running, single-robot third-person follow. Training stays parallel.

- Active batch: `python3 scripts/p3_19_train.py`, exec session 48387. GPUs 0/1, fresh seeds 1/2, 1024 environments each, 3000 updates each. Config `configs/p3-19-long-easy.json`. Outputs `artifacts/p3-19-long-easy-seed{1,2}`. Native 64-episode evaluation and single-robot follow recording run automatically.
- Easy/medium/hard shared inclined/turning maps have 11 surfaces and ten transfers (~4.6/6.5/8.6 m). Transfers are not automatically jumps. Flight events are measured independently. Episode limit 30 seconds; standing until timeout is not a successful demo.
- Early updates ~500 show zero first-surface progress and exploration collapse. GPU 2 checkpoint-500 diagnostic: first attempt omitted matching config and failed restore; preserved. Retry `p3-19-long-easy-seed1-interim500-retry1` uses correct config, session 18052. Inspect before choosing next curriculum. GPU 3 free.
- P3-18 short main pilot was NEVER launched; do not launch it. Prior P3-16/P4-03 batches are finished. Do not resume endless straight-hop tuning.
- P3-19 learning smoke retry1 and medium/hard physical geometry probes passed. Smoke follow video is 30s stationary novice behavior, zero completion, not the requested final demo.
- Web updated for continuous-course metrics and schema-2 diagnostics, follow recording now includes force/action/progress traces. UI build and nine backend integration tests passed. Web service restarted, health OK on 18710.
- Current controller is an independent front/rear target Tracker using scripted training contacts, not an autonomous Planner. No long-course completion established yet.

--- Previous chronological notes ---

# Current work after this completed batch

P3-16 currently training two seeds1200updates/1024env via scripts/p3_16_train.py, execsession86316, logartifacts/p3-16-training-batch.log. Each follows with full-gap50cm translation and continuous regression evaluations; native reach video also automatic. Script asserts curriculum changes atupdates301/601. Read p3-16-protocol.md. Short12update64env smoke/native evaluation passed. FrozenP3-15seed1 physicalgap probe0/64; sixfirst/lastclone PhysX rays verify actualemptygap withcatchfloor at-0.5m andplatforms0m. Gap parentartifact/eventaudit passed.

Vectorized gate GPU8hop evaluation exactlymatches P3-11seed2 all64records,448transitions and20tracechannels; GPUmicrobenchmark now running onsession82076, GPU2 under run_job. Default remains reference pending measuredtimings. This paragraph supersedes prior active state below. Continue autonomously, do not stop atjoblaunch.

# Current autonomous research batch

User: continue until the final parkour objective or explicit stop. Do not finish the turn merely on launch or one small phase. Read actual process/supervisor/artifact state before repeating jobs.

COMPLETED: all26 tasks succeeded, reports generated. History both seeds0/64 all common suites; zero controls retain some course capability. P3-15 reach seed1 succeeds through25cm,seed2 poor. See p4-03-findings.md and p3-15-findings.md.

Historical command: `python3 scripts/research_course_history_batch.py > artifacts/course-history-batch.log 2>&1`
Exec session21031, started after source commitf6c9192. Six training jobs (all800updates/1024env): P3-15 longer jump seeds1/2; P4-03 history and zero control seeds1/2. Same-seed P3-08 mapped source checkpoint800. Global new-step budget117,964,800. Four workers own GPU indices only through run_job UUID leases. Training priority; completed jobs enqueue their common evaluations, so free workers backfill evaluations while other training continues. Plan: artifacts/course-history-batch-plan.json. Completed/failed state: artifacts/course-history-batch-state.json. This finite batch runner is not a complete resource broker or an unbounded autonomous service.

Each train includes native evaluation+64-robot video. Then P3-15 has4 common evaluations (reach and continuous for2seeds); P4-03 has16 (uniform8,friction0p2,friction0p05,continuous for4models). Total26 queued tasks plus6 native evaluations inside train wrappers. Reports scripts/p3_15_report.py and p4_03_report.py run only after all26 tasks succeed. Failure stops new admission but lets already executing jobs finish; artifacts are never overwritten. Investigate/recover missing tasks rather than rerunning successful training. State is persistent evidence, not automatic process resume.

Completed prerequisites: history clock/reset/mask/shared-normalization/initial-mean equivalence tests3; legacy fork tests4; history64env12update smoke and2update resume with native videos; longer-distance64env12update smoke/native video. Main training and common evaluations are complete.

Research status:
- P3-11 uniform8 hops/1.2m foot goal: mapped seed1=48/64 seed2=64/64.
- P3-12 small alternating14.5/15.5cm: seed1=53/46,seed2=64/64 by pattern.
- P3-13 opt-in1cm elevation: upseed1=34/64,upseed2=15/64,downseed2=60/64. All-zero seed2 exactly matches old episode records/all existing200Hz trace channels. Actual first/last clone bounds and target-Z/landing-height errors audited.
- P3-14 strict airborne reach: bothseeds15cm16/16;20/25/30cm each0/16. P3-15 broadens training15–30cm on a wide deck, not physical-gap success.
- P4-02 alltraining/eval/report completed. Low-friction/control effects depend on seed and friction; regression remains. No champion. See p4-02-comparison.md and findings.
- P4-03 compares140ms history against zero additional inputs at identical535-input architecture. Shared66-channel normalization; seven validity bits; no contact-free/sensor-only claim. Current observation still contains oracle body state and contact-derived phase.

Geometry next: a simultaneous four-foot transfer between two whole-body platforms needs translation greater than calibrated front/rear footprint span+departure/landing margins. Measured span0.3735075m; with2cm margins a positive gap needs >0.4135075m. A50cm translation permits about8.65cm physical gap under this simple layout. Thus30cm reach training is a capability stage, not already a whole-body gap demonstration. Do not relabel per-foot pad gaps as that result.

Monitor18710 active, pagination verified and course completion panel deployed. New stages use phase:P3/P4 and explicit step tags. Keep64-robot camera_side4 overview plus supplementary individual closeups when useful, all in result with detailed titles. Continue to actual terrain/capability progression after this batch instead of waiting for every minor regression to disappear.

## User steering supersedes next-step suggestions above

User reasserted video EZbM594T3c4 target: current per-foot straight pads too narrow a research scope. Read docs/parkour-target-review-2026-09-12.md and docs/p3-18-continuous-tracker-contract.md first. Downloaded video for internal review (not copied into our performance result), inspected full10s montage and key1s slope/turn sequences. New shared_terrain module/2CPUtests and actual Isaac mixed terrain probe completed: artifacts/p3-17-shared-mixed-geometry,7center/normal rays passed; preview underresult/previews explicitly no-policy. PairTargetProgress prototype2tests passed, not yet connected to a controller. Future priority is new continuous front/rear shared-surface Tracker, not additional fixed full-gap/P3-17 training. P3-16 currently active finite run should finish and audit. No default contact-gate implementation changed; GPUmicrobenchmark~13.2ms reference/~0.6msvectorized, whole-controller speedup not claimed.

P3-16 CLOSED: session86316 completed both1200-update trains/native evaluations plus4 common audits. Reach native only15cm successes (13/13 and7/13),all25cm+0;fullgap0/64 both,continuous0/64 and24/64. Results/findings in docs. No further straight tuning. P3-18 newenv continuous_tracker_task.py uncommitted prototype105obs. GPU2 run_job smoke initialfailedclassattribute, fixedtoexplicitA1asset; retry1session92303 active:artifacts/p3-18-continuous-tracker-smoke-retry1. Zero-action64env/200steps physics+renderer test, not training. Check before any furtherGPU2job. Pending: verify/fix smoke, then integrate new task learning/evaluation with new contract. Shared surface scripted targets use separate final fore/hind contacts to avoid impossible coincident fourfoot stance. No fullgap training implementation was added after usersteering.

P3-18 updates: zero-action retry1PASSED, then newtask training/evaluation integrated: p3-18-continuous-learning-smoke12updates64env passed including native64eval/video/result and scripts/audit_continuous_evaluation.py. Resume2update smoke currentlysession66084 onGPU1 atartifacts/p3-18-continuous-learning-resume. Before main pilot wait for this+nativeevaluation and audit. New configconfigs/p3-18-continuous-shared.json, taska1_continuous_tracker_v1,105obs. Proposed next two policyseeds1/2samegeometryseed1,1200updates1024envfresh notfork. Current codechanges uncommitted until checkpoint. Do not silently call old jump successgates or newscriptedtargetbuffer autonomous Planner. New continuous diagnostics module preservesphysicsrate root/foot/force/actions/targetindices; old diagnostics untouched. Physicsrayqueries verify allnoninitialtargetpointsfirst/lastclones. Keynextwork: generalization evaluation override/newgeometry, richerinitialterraincurriculum, meaningfulrawtargetevents andlearned progress; no claim newpolicy performsparkour yet.
