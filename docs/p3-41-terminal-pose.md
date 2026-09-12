# P3-41 — Explicit hybrid terminal pose evaluation

P339control800 traverses60targets in12.5s, but rocks atgoal. Originaltrace includes slow, centered periods with>=3validfoot supports. Evaluation-only TerminalPoseHold waits forbothfinalpairacceptances,>=3validsupports, rootXYerror<.12m, linear speed<.3m/s, angularspeed<2rad/s, tilt<15deg for3consecutive20mssteps. It then blends current clipped policy actions over15steps into the calibrated standing joint references, through the unchangedPDactuators and limits.

This is a fixedRLtravel policy plus an explicit terminal pose controller, not learned RL stabilization. The controller metadata, jointtargets, gate and handofftime are stored and titles/UI explicitly label the hybrid. Existing physicalsuccess/failure criteria stay unchanged. One64episode development evaluation onGPU2session12850. Dwell/blendunit testpassed. Not adopted until actual outcome reviewed.

PureRLresearch continues separately: P339braking resumes800→2400 onGPU3 (session13116), with unchangedconfiguration/optimizer/normalizer restored; this is additional learning, not hybrid policy training.

Settled gate evaluation:0/64success,0handoffs; original traces show supported contact moments have angular rocking5–7rad/s, so the2rad/s gate neverfires. Contact-capture variant retains centered/slowlinear/tilt/support conditions, allows angular<8rad/s, and triggers afterone supportedcontrolstep; still15stepblend and unchangedlimits. Actual64episodeevaluation:19/64success,30handoffs. Fixedenv0success at14.36s,12.505s travel, handoff13.72s; auditpassed. This is the first recorded successful long-route hybrid completion, not high-rise jumping or robust pureRL completion. Artifact p3-41-long60-contact-capture and detailedresult archive retained.
