# P3-21 — Body progress signal on the same long course

P3-20 at update 500 still has zero live front/rear accepted indices with std held at its .12 floor. Test one additional motion signal, retaining the P3-20 map, full precision schedule, exploration bounds and seed.

At each control step, cache the current target quartet's mean plus the measured calibrated root-to-mean-foot offset as a body waypoint. Add 10 × (root distance before physics − root distance after physics) to reward. Both distances use the same cached waypoint. Target-buffer advancement itself therefore cannot generate this reward, and a stationary state or unweighted round trip returns zero. This is a development shaping intervention, not a dynamics controller or a claim of policy-invariant reward shaping under discounted returns.

No scripted joint motion, state teleport, physical reset between contacts or extra action input is introduced. The strict contact/geometry/final stabilization gates remain unchanged.

Validation: stationary, round-trip and bookkeeping-switch checks passed; 12-update 64env smoke, native strict evaluation and trace audit required before main pilot. Initial main budget 600 updates ×1024env×24 steps, then inspect first-surface progress before extending toward 2400 updates. Do not automatically extend a zero-progress policy. The full schedule is retained, so a 600-update checkpoint is still an intermediate curriculum model; evaluation remains .06m.

The reference paper's Table S4 separately uses contact and bounding-style incentives; our simpler baseline omitted bounding reward. If this body-progress intervention does not initiate stepping, test a documented pair-contact/bounding intervention rather than increasing this weight without evidence. This is not an exact reproduction of the paper's reward or training setup. Source: https://arxiv.org/html/2506.02835v1#S0.SS5
