# P3-46 — Controlled motion and truly disjoint courses

User asks to retrain more realistic motion, increase terrain difficulty, and dynamically plan3–4steps. The final requirement is NOT satisfied by the current scripted Tracker.

Implemented motion_control_v1: per-second horizontal speed error cost6 around1.8m/s during travel, zero target at terminal; joint reference slew8or12rad/s; joint speed soft cost0.02 above16rad/s. These are engineering starting values, not measured hardware constraints. Controller still uses existing DC motor envelope and PD gains. Resume rejects altered motion contracts; explicit forks preserve lineage. No change for old configs without the field. Applied command remains in the policy observation.

Twelve-update64env smoke results: rate8mean0transfers,rate12mean4.64; disjoint easy/medium initially0. All physics trace audits pass. Initial performance collapse is expected to require adaptation and is not a success claim.

Running:
- GPU0 p3-46-rate8-train:2000updates×1024env, session19708.
- GPU1 p3-46-rate12-train:2000updates×1024env, session25575.
- GPU2 p3-46-discrete-easy-train:600updates×1024env,12rad/s, session37810.
- GPU3 p3-46-discrete-medium-train:600updates×1024env,12rad/s, session28484.
All explicitly fork P340rise05checkpoint1600. Unlike the smoke disjoint configs, main disjoint pilots use12rad/s. Do not treat smoke/main as a single unchanged trajectory. All four initialization/observed-metric audits pass.

New discrete_parkour_v1:17surfaces,16actual gaps, no overlapping approaches; base gaps18/35/55cm, increasingly tilted/raised/turning surfaces. Gap clearance measured using full oriented cuboid horizontal projection, not center spacing. Exact generator validation, target exposure, and separation tests pass. Lengths15.30/18.65/22.39m. Easy is an entry pilot, not a guarantee of10seconds travel. Difficulty catalog in result/scenarios/discrete-parkour-difficulty-designs.

New receding_surface_beam_v1: geometric3/4step beam search using current surface, root position, velocity, goal and blocked surfaces; explicit budget/no-plan behavior. Tests cover ID ordering independence and loss of route on blocked surfaces. This is a standalone shadow prototype; NOT connected to Tracker actions, NOT a physical rollout planner. Critical next work: candidate foot/contact timing contract, current-checkpoint simulator rollout, state restoration validation, runtime deadline/fallback and closed-loop execution. Do not label current videos as autonomous planned parkour.

## Persistent bounded continuation
scripts/p3_46_continue.py process2439797 waits for both constrained main evaluations and disjoint pilots, audits them, ranks constrained candidates by development full success then mean transfers. If neither reaches mean3transfers, records NEEDS_REVIEW and stops. Otherwise GPU2/3 train1200update disjoint successors (P347) from selected constrained parent with identical motion contract, followed by64episode evaluation, trace audit and follow video archive. Maximum2successorruns, no automatic champion promotion or infinite retries. Status artifacts/p3-46-continuation.json, log artifacts/p3-46-continuation-driver.log. Both tiers share the parent; this is curriculum engineering, not universal-policy proof.
