# P3-35 — Evaluation-only terminal RL policy bundle

P3-29 achieves64/64strict point-course completions, while P3-30medium reaches all ten surfaces but does not settle (0/64full). Test whether its travel skill can reuse the verified terminal stance skill. Two independent fixed PPO policies/normalizers are evaluated; no updates or training rollout mixing occur.

Primary travel checkpoint: P3-30seed1 update1200. Terminal checkpoint: P3-29seed1 update800. Handoff requires both groups accepted on the final surface, at least two currently valid foot supports, rootXYwithin0.3m of goal, linear speed<1m/s and tilt<30deg. It latches only until that first episode ends. No intermediate transfer or airborne handoff. Actual environment success/failure/stabilization gates stay unchanged. The secondary checkpoint hash, gate, used flag and handoff timestamp are recorded; results and video titles identify the composite bundle rather than a single checkpoint.

Policy loading preserves RNG state and validates robot/calibration/action/105-channel observation meaning. A unit test rejects premature/unsupported/fast/tilted/done handoffs. Simulator evaluation, prefix trajectory inspection and the existing physical trace audit are required before adopting this optional execution bundle. This is not an autonomous Planner or reproduction of the reference controller.
