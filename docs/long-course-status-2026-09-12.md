# Long-course research status — 2026-09-12

Latest user objective: varied difficulty maps, roughly ten dynamic movements/jumps, more than ten seconds of actual scenario traversal, one robot recorded by a third-person following camera. PPO training remains parallel. Videos are original fixed-first-episode frames, with no padding or stitching, and detailed result/ archives. No qualifying final dynamic demo yet. Current contact buffer is scripted, not an autonomous Planner.

## Confirmed results

- P3-25 seed1/2: corrected rear startup and either-foot60ms progress;2400updates1024env per seed with25→18→12→8→6cm contact training. Native64episode strict6cm: seed1 all reach acceptedfront/rear10, mean1actualjump,0fullsuccess; seed2 mean9.78completedtransfers,0jumps,0fullsuccess. Final stance remains incomplete. Both audited; no extension unchanged.
- P3-27 seed1: explicit800update lower-noise fork from P3-25 update1200. Native0/64full,mean9.8125transfers,0jumps,no falls. Fixed robot reaches front10 in2.4s then waits. Not a10s traversal demo.
- P3-28 seed1: exposed shared-surface region gate, distinct from6cm point accuracy. Native29/64full including terminal stabilization, all64reachaccepted10,0falls,0jumps. Fixedvideo robot timesout; successes are not selected into that video. Clones on identical geometry/initial state are not independent terrain samples. Artifact/physics trace audit passed.
- P3-29 terminal-style gating smoke: initial highLR/reset-noise smoke regressed. Matched parent adaptiveLR0.000050625 and cap.12 retry retainedmean10transfers,0full,meanpoint error3.21cm; audit passed. Main800update point refinement onGPU2, session15380, artifacts/p3-29-terminal-stabilization-seed1.
- P3-30 medium: direct frozen P3-25 point parent fails first step. Region transfer smoke registers one flight then fails (.62s). Main1200updates onGPU3, session19028, artifacts/p3-30-medium-regions-seed1. Byupdate429, terminated training episodes averaged5.66transfers and1.31jumps; not yet frozen evaluation. Interim400 evaluation onGPU1 underway. Same checkpoint has not yet demonstrated medium completion.
- P3-31: generated20/30/40transfer maps and safe clone spacing; ten-transfer geometry unchanged. Frozen region parent on40easy fails around11transfers. Main800update40easy endurance fork onGPU0, session52766, artifacts/p3-31-extended-regions-seed1. This is an endurance/capability test, not a claim that40transfers mean40jumps or the final dynamic scenario.
- P3-32: explicit50%easy→medium geometry preparation smoke/native/audit passed (2.53transfers,0full/0jumps). Full medium training is already progressing, so the preparation main run is a fallback rather than a required extra stage.

## Execution / next decisions

Use scripts/run_job.py UUID leases; native evaluation and result collection follow each train before GPU release. Do not steal GPU2/3/0 before their wrappers finish. Monitor at18710. GPU1 currently short evaluations. P3-25 continuation driver53047 is complete. No teacher transfer was adopted. All policy forks retain parent hash and copy actor/critic/normalization with fresh optimizer/RNG; explicit LR and exploration schedules are recorded. Do not resume across contact/reward/geometry changes.

Prioritize medium dynamics and then a longer medium route once measured progress supports it. A surface transfer is not automatically a jump: choose the eventual length using observed traversal time and jump count. Do not keep polishing easy point accuracy as a prerequisite for every new scenario. P3-29 is a bounded side comparison, not the main progression path.

Duration measurement now distinguishes episode length, body-speed>0.15m/s duration and travel duration before both pair targets enter final stance. The extra travel phase prevents terminal rocking from counting as prolonged traversal. Eligibility contract v4 requires full success, ≥10transfers,≥8measuredjumps and≥10travel-motion seconds. No final test set has been used; all changes are development-stage, and no champion promotion occurred.

## Artifacts and verification

result/scenarios/ten-transfer-difficulty-designs contains dimensioned PNG/SVG and exactJSON for easy4.64m,medium6.52m,hard8.59m designs. These are geometry designs, not robot performance. scripts/summarize_long_course_motion.py reanalyses original traces without modifying old reports. Raw body-motion time can include rocking: do not call it route travel time. The frontend separately labels region and point evaluation and moving duration. Six shared-geometry tests, nine old/new fork tests, region/terminal-style tests, actual simulator probes and native trace audits have passed where reported. Rebuild frontend after latest travel-duration line before final handoff.

Update20:56KST: P3-29main completed and audited64/64strict6cm fullcourses,0jumps,mean3.10sepisode/2.435stravel. P3-30interim400 frozen16evaluation reachesmean7.06transfers and2flights in2.74s, then nonfoot failure; audit passed. These are concrete progression, not qualifying long demo. P3-32smoke motion/travel duration independently matches200Hz traces. No preparation main run: full medium is already learning. Next P3-33 medium40 fork fromP3-30update600 uses transfer/jump ratio as a design guide: roughly40foot transfers may yield~10real flights and>10s, to be measured rather than assumed.
