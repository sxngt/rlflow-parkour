# P3-48/49 — Continuing discrete motion learning and physical candidate evaluation

2026-09-13. User requests autonomous continued design/execution toward genuinely dynamic parkour and online3–4step planning; no routine confirmation needed.

P346 completed. Rate8fullsuccess1/64,rate12zero. Firstrobot speedp95=2.35/2.823m/s; actual joint reference slew≤8/12rad/s and jointspeedp95=12.2/14.7rad/s. Thus the slew limit works, while1.8m/s is only a soft reward target and has NOT become a hard body speed bound. Discrete easy pilot600 reaches6/16,medium2/16 frozen mean; neither completes. P347 automatic transfer from rate8 is active onGPU2/3,1200newupdates.

P348 resumes the existing600update discrete pilots,1800additionalupdates,total2400, onGPU0easy/session59737 andGPU1medium/session11513. Keeps12rad/s contract and optimizer state. Compare this continuation to the separately initialized P347, not as an isolated algorithm ablation.

## P349 physical four-step candidate assay

New evaluation flag --four-step-candidate-probe installs9candidate foot-target sequences with surface-local XY offsets{-8,0,+8}cm×{-4,0,+4}cm on the first4intermediate surfaces. Same offset for all4steps in each candidate: a deliberately limited candidate family, not exhaustive sequence search. Candidate4is the unchanged zero offset. Each candidate has8replicas (72env), the same frozen checkpoint and calibrated episode start. Every candidate foot center is checked against the selected surface's existing usable margin. Terminal stance and all other surfaces remain unchanged. No reward/controller/actuator change in this assay.

Per-environment goal buffers are used consistently in the current targets and next-target observations. Legacy shared-buffer behavior is tested for equality. Original first-episode physical traces and unselected env0follow MP4 are recorded. candidate-rollouts.json separates first4transfer reach from fullcourse success; no false4step prefix promotion. Full course evaluation still runs to its original end.

This advances beyond geometric filtering to actual Tracker-driven simulation, but it is NOT an online planner: no mid-flight snapshot copying, branching simulator restoration or real-time deadline claim. Current surface sequence remains fixed; candidates change precise foot goals. Next necessary step is to validate snapshot restore including sensor/actuator/progress/history state in an isolated simulator, then evaluate multiple plans from the observed state and commit only a short prefix. Search horizon and execution lookahead are distinct; policy currently sees2targets per pair.

Persistent P349driver process2470102 waits for P347training+evaluation GPUrelease and audits, then usesGPU2/3 to evaluate P346discrete easy/medium checkpoint600 with72env. At most2evaluations; no unbounded retry. Status artifacts/p3-49-probe-driver.json/log. P346continuation driver remains responsible for P347 only; GPUleases remain authoritative. No active jobs were interrupted.

## Completed candidate assay and P350 replay validation
P349easy: candidates0–6reach fourth surface8/8, candidate7=4/8,candidate8=0/8. Zerooffsetcandidate4 reachesmean6surfaces;allfullcoursefailures. P349medium: all9candidates fail beforefourth surface, mean1–2transfers. Both72episode trace/artifact audits pass. Supports candidate filtering value in this limited family, not final RQ1statistical proof.

P350reconstructs prefix by replaying sourceenv0's applied actions from calibrated start, using the identical checkpoint and config (numenvs/tags excepted). Checks trace hashes, current root/joint state and target progression before candidate branch. Does not restore a PhysX solver snapshot and incurs full prefix re-simulation cost.

50step/1s prefix failed fixed tolerances: easy maxjointvelocityerror10.577rad/s;mediumjointpositionerror0.020486rad exceeds0.02rad. These original runs predate the additional orientation/angularvelocity checks and are retained as failed attempts. No candidate execution after rejection.

20step/0.4s updated validation includes rootorientation andangularvelocity. Easy rejected angularvelocityerror0.15255rad/s vs0.15limit; not loosened. Medium passes all72replicas: rootpositionmax0.000191m,velocity0.000907m/s,jointposition0.000540rad,jointvelocity0.08154rad/s,orientation0.000977rad,angularvelocity0.007913rad/s. Medium then physically executes4surface candidate horizons; trace/artifact audit passes. This is a validated short-prefix research assay, NOT online planning. Contact solver hidden state is not independently validated; candidate outcomes still require conservative interpretation.

P349/P350 candidate report now uses candidate_horizon_reached and required_surface_index for noninitial horizons; old P349 artifacts retain original first_four_transfers_reached field. Candidate4remains zerooffset. All recordings use fixedenv0, not success selection.

## P351 automatic next curriculum
Driver scripts/p3_51_continue.py process2479788 waits for audited P348finalresults. Two1200update successors onGPU2/3. Per-tier mean≥12/16extends that tier to24transfers(discrete_parkour_v2); otherwise16retained. If mediummean<8 and easymean≥12, medium initializes from easy policy. Othermotion/robot/observation contracts unchanged. This is explicit curriculum engineering, not automaticchampionpromotion. Original16map constructor unchanged;24map preserves first16nonterminalsurfaces. Easy24length>22m, supports but does not guarantee10sactualmotion. Status artifacts/p3-51-continuation.json.
