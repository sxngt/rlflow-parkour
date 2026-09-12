# P3-25 — Either-foot progression on the corrected startup sequence

Compare with P3-24 by changing only intermediate pair contact quorum from both to either. Require at least one foot's selected-surface/normal-force/precision validity continuously for60ms; update the pair's target together. This matches the reference's stated target updater more closely than our original both-feet condition. It does not imply that both feet achieved every intermediate target, so the quorum is explicitly reported.

Keep the new front-stance initial rear target, same ten-transfer easy geometry, same PPO, reward and contact precision curriculum. Full course success still requires final four-foot precision/support and body stabilization, and dynamic demo eligibility still requires actual time and measured jumps. The initial800update budget uses1024env and fresh seed1. Smoke12updates64env, strict native64episode evaluation and physics trace audit passed. Inspect progress before extending.

At update39 seed1 showed live mean front accepted index0.02148 (broad training radius.25); the matching P3-24 both-foot condition had zero front progress at that update. This is an early development signal, not strict evaluation or statistical proof. Added independent seed2 with the same800update budget onGPU3 to check replication.

Both800update pilots finished. Strict6cm native64episode evaluations: seed1 meanfront1.421875/rear1.3125, completedtransfers1.3125,0fullsuccess,0measuredjumps; seed2 front1/rear−1,0transfers,0success,0jumps. Replicated clones on fixed geometry are not64 independent terrain samples. Both artifact/200Hz trace audits passed. Training radius18cm had livefront~8.9, so neither broad training progress nor actual run time is a final demo.

Both passed the recent100update maximum-livefront≥1 continuation admission check (not a mean or sustained-progress proof). Same-config resumes800→2400 now run through12/8/6cm precision stages. Driver scripts/p3_25_continue.py ownsGPU1/3 through native evaluations.
