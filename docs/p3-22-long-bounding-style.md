# P3-22 — Pair-support style intervention

P3-21 completed its 600-update pilot without live front/rear target progress; its native strict evaluation is collected before the next main pilot. Do not extend P3-21 unchanged.

Add 2 reward units per simulated second when FL/FR share contact status and RL/RR share contact status, except simultaneous four-foot stance. This includes all-foot flight. The condition follows the bounding-style idea in Table S4 of the reference paper (https://arxiv.org/html/2506.02835v1); other rewards, robot, 50Hz controller, geometric strictness, and PPO settings remain our own implementation. This is not paper reproduction.

All other conditions match P3-21 (body waypoint progress10, contact precision schedule, bounded exploration). Start with a fresh seed1 policy, 1024 environments, and 800 updates, inspecting progression before continuation. The base config retains its full2400update schedule. Native evaluation remains strict6cm and the whole ten-transfer30s map. Initial smoke and physics trace audit must pass before main training.

This reward may produce in-place bouncing or standing on one pair. Those are recorded as failure to progress; style reward is never a jump count, contact acceptance or course success criterion. The measured jump detector and final dynamic demonstration gate remain independent. No teleportation or scripted robot movement is used.
