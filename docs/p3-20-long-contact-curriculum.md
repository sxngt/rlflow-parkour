# P3-20 — Learning to leave the start on a ten-transfer shared course

P3-19 checkpoint 500, seed 1: 0/16 completed courses, 0 front/rear accepted surface transfers, zero measured jumps, all episodes timed out at 30s. Follow recording shows the robot holding its starting stance; mean final error 0.1574m. Training seeds 1/2 show declining policy entropy and zero contact progress near update 900. These are failed development observations, not a ten-second parkour demo.

Keep the ten-transfer easy map, physical model, 105 observation inputs, asynchronous front/rear targets, fixed initial state, and reward unchanged. Test a combined contact-precision curriculum plus persistent exploration intervention. This pilot cannot separately attribute the effect of those two changes.

Training radius: .25m at update 0, .18 at 400, .12 at 800, .08 at 1200, and .06 at 1800. Existing surface-local containment, positive normal force and contiguous contact duration remain required at every radius. Reset incomplete episodes at schedule boundaries and record the discarded boundary. Evaluation always uses the strict configured .06m radius; broad-radius training successes are not evaluation successes. Checkpoints store the next schedule radius and completed update.

Bounded Gaussian std .12–.5, fresh policy initialization. 2400 updates ×1024 environments ×24 steps = 58,982,400 steps per seed. Initial pilot seed1 on GPU3; add replication after inspecting progress, rather than filling the spare GPU with an untested duplicate. P3-19 baseline jobs on GPUs0/1 remain unchanged.

Smoke: 12 updates ×64env, native strict 64episode evaluation and physics trace audit passed; zero completions as expected for the novice. Explicit restore probe is separate. New final videos follow env0 through only its first episode and retain synchronized contact/action/progress records. Videos and full report are archived under result automatically.

Frozen evaluation-only difficulty/seed overrides now support easy/medium/hard ten-transfer courses without mutating the checkpoint's training configuration. Use a development held-out geometry seed (101); do not label these results a locked final test. Physical geometry inspection is required on each generated course.
