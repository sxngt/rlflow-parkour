# P3-39 — Ten gaps with longer real approach segments

The40transfer medium route is traversed in~8.4–8.8s, so episode timeout30s cannot certify10s travel. The new long_ten_gap_course_v2 preserves10gaplocations and adds five approach transfers per gap (61surfaces/60transfers). The original40transferv1 geometry remains byte-identical. Catalog result/scenarios/ten-gap-60-difficulty-designs contains exact difficulty geometries. Width multipliers1.25/1.5 also permit gap-only difficulty changes independently of initial slopes/heights.

FrozenP336800 onmedium60 reaches48/60,~9.81s travel,0full. The widergap125 frozen60 failsfirstgap at5/60. Audits passed. This is development feedback, not held-out generalization.

Paired800×1024 run fromP337bounded800 onmedium60: terminal_motion_cost2 vs0. Cost applies only when both target indices select finalstance; it penalizes linear speed squared plus0.1×angular speed squared per simulatedsecond. Current pose/contact criteria and in-route rewards are unchanged. This aims to brake before falling or rocking at the finalplatform. Fresh optimizer with parent adaptive LR0.00011390625, std.18→.12. Integration smoke and native audits passed; GPU2braking session56763;GPU3control30775. Training continues, no successful long demo yet.

Both initial1024env main attempts failed before training at the physical ray audit: world-coordinate rounding error54.9micrometres exceeded the constant50micrometre threshold. The61surface course requires36.9m clone spacing, putting edge clones hundreds of metres from origin. The audit now uses50micrometres plus two float32ULPs per coordinate axis, with a hard1mmbudget ceiling; collider identity and normal alignment checks remain. Recorded tolerance for every ray. No contact success threshold, collision geometry or policy behavior changed. New attempts -r2 onGPU2session11943/GPU3session99605.

The -r2 physical audit passed480rays: max position error0.06939mm vs coordinate-derived bound0.22263mm. Both jobs reached real PPO updates; initial failures preserved. This correction changes ray verification precision only.
