# P3-45 — Motion realism diagnosis

User reports unnaturally fast motion. Prioritize diagnosing actual physics and command smoothness before more completion-only optimization.

P340rise05native fixedenv0:306frames at25fps=12.24s; replay timestamps0..12.20s with40ms spacing. No playback acceleration. Physics-rate horizontal root speed mean2.76156m/s,p953.25227m/s,max3.48955m/s; measuredXYpath33.8214m.

At50Hz control, normalized actions×0.5rad give absolute joint target changes p95=0.65869rad (37.74deg),max0.98095rad per20ms. This is a requested target change, not actual joint movement. Existing rewards prioritize pair acceptance (2each) and body progress(weight10). Action-delta penalty0.01 is multipliedby0.02s, and no intermediate target-speed or command slew limit exists. Strong reward imbalance is a causal hypothesis, not a completed ablation.

A1 uses stock DC motor torque-speed envelope33.5Nm/21rad/s,PD25/0.5;21rad/s is the model no-load speed parameter, not proof of a hard physical angular-speed bound. No hardware dynamics validation.

Added physics-rate joint position, velocity, target, computed torque and applied torque traces (schema4), preserving controller/reward behavior. P345native64evaluation records actual motor behavior before selecting a new constraint/reward experiment.

P344control2400 frozennewseed evaluations:easy101=0/64,medium101=0/64,easy102=0/64,medium102=7/64. No universal terrain policy claim.

Completed64episode actuator audit: fixedenv0 actualabsolutejointvelocity p95=16.8134rad/s,max25.3741rad/s. Computedtorque absolute p95=18.1526Nm,max31.9683Nm;appliedtorque p95=18.0155Nm,max31.9683Nm. Torque-speed clipping changes3.1999%joint-physics samples (difference>0.001Nm). This does not establish hardware feasibility or continual saturation; peak joint velocity exceeds21rad/s no-load parameter, which is not configured as a hard safety speed bound. Physics trace/artifact audits pass.
