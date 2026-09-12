# P3-29 — Bounding reward ends at terminal stance

P3-25/27/28 often hold advanced target indices but have no full-course success. Existing bounding-style reward pays2/s for front-only or rear-only support, even when both pair targets are already the final platform. This conflicts locally with the required four-foot terminal stance. It is a suspected incentive problem, not yet proof of the sole failure cause.

Opt-in bound_reward_scope=travel_only disables only this style term when both pair target indices reach the last surface. Earlier travel reward, foot point accuracy, nonfoot termination, dynamics and final stabilization gate remain unchanged. Old scope=all remains default and checkpoint-compatible. Scope changes are explicit policy forks with new optimizer/RNG and recorded old/new scope; resume rejects them. Not an isolated ablation because the fork restarts optimizer and exploration schedules.

Planned parent: completed P3-27 seed1 update800 (strict6cm). New800update1024env bounded budget,6cm throughout, exploration cap.18 then.12 at400. Validate fork/init, headless smoke and native evaluation before main pilot. Keep P3-28 region result separate from6cm point success. Final demonstration also requires actual run duration and measured dynamic events.

Initial64env smoke passed integration but regressed to0.83meantransfers. It reset adaptive learning rate from parent0.000050625 to0.001 (~20x), and increased noise cap.12→.18. Before the main run, use a separate retry with explicit initial LR0.000050625 and constantcap.12. New fork validator permits only finite positive explicit learning-rate changes (other PPO/network contracts fixed). This engineering correction is recorded rather than rewriting the first smoke artifact.
