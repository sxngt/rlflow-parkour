# P3-25 — Either-foot progression on the corrected startup sequence

Compare with P3-24 by changing only intermediate pair contact quorum from both to either. Require at least one foot's selected-surface/normal-force/precision validity continuously for60ms; update the pair's target together. This matches the reference's stated target updater more closely than our original both-feet condition. It does not imply that both feet achieved every intermediate target, so the quorum is explicitly reported.

Keep the new front-stance initial rear target, same ten-transfer easy geometry, same PPO, reward and contact precision curriculum. Full course success still requires final four-foot precision/support and body stabilization, and dynamic demo eligibility still requires actual time and measured jumps. The initial800update budget uses1024env and fresh seed1. Smoke12updates64env, strict native64episode evaluation and physics trace audit passed. Inspect progress before extending.
