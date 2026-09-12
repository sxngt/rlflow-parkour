# P3-52/53 — Discrete completion and speed-reward balance

P352frozen1700checkpoint from P348easy:64/64fullsuccess on original16gap course. Fixedenv0:7.08sepisode,6.195stravel,16transfers,17cleantravelairborne,2strict3cm-risejumps. Mean horizontal speed2.166m/s overepisode,p952.803,max3.029. Command slew12rad/s remains active. Same-geometry clones, not terrain generalization. Physical trace audit passes. Follow frame inspected and result/long-course-follow/README.md updated with direct video link. No10sor10largejump claim.

P352medium1700:0/64,allreach4transfers. Easy1700frozen transfer to24gap extension:0/64,firstrobot15transfers. Shape of original terminalsurface16 becomes intermediate in extension; longer-course behavior requires training. Exact16map remains unchanged. These evaluations are development probes.

P353motivation: body-progress reward10permetre grows withspeed, opposing quadratic speed cost6*(v−1.8)^2. Ignoring other terms, these two alone have optimumv=1.8+10/(2*6)=2.633m/s; this algebra is NOT a fit of full PPO behavior. Discrete contact progress and discount also influence speed. Thus1.8softtarget was never a hard speed guarantee.

New optional motion_control_v2 caps positive body-progress reward atweight*targetspeed*dt while retaining negative backtracking cost. Also compare speedcost20instead6. Robot,normalization,action envelope,12rad/scommandrate,observationchannels unchanged. This is a reward-package comparison, not isolation of each component. Oldv1configbehavior preserved; explicitforkrequired forversionchange. Unit tests verify cap and retained negative penalties.

P35312update64env integration smoke passes,64/64fullsuccess,firsttravel6.235s; too short to infer speed-improvement effect. Physics trace audit passes.

Persistent paired main comparison scripts/p3_53_speed_compare.py PID2484961 waits for P348GPU0/1training+evaluationrelease. Two1200update1024env runs, same P348easy1700parent, fresh optimizer and identical initial settings. GPU0cappedv2/cost20;GPU1unchangedv1control. This runs alongside P351curriculum onGPU2/3. No automatic model promotion. Driverstatus artifacts/p3-53-comparison-driver.json andlog. Coarse driver may remain WAITING untilresults; individual run records/leases are execution authority.
