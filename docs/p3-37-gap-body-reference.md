# P3-37 — Body reference during explicit gap crossing

The prior reference averages current fore/rear foot targets. While the fore pair targets a gap landing and the rear pair remains at departure, this can guide the body into the gap. This is a suspected reward conflict, not an established cause.

The optional `body_progress_reference=gap_landing` uses the selected landing surface center plus calibrated standing root height while a fore target marked gap_landing is pending. All other steps retain the original midpoint. The reference is cached before physics and used for both pre/post distance, so target switching without motion earns zero. No action, observation, contact acceptance or failure limit changes. Resume across references is rejected; forks record both contracts.

Matched 2×2 engineering pilot, one seed, each800updates×1024env×24steps, same P3-34prep75checkpoint800, full nominal45cm ten-gap map, parent adaptive LR7.59375e-5 and identical std schedule:
- P3-36 control: legacy mean / midpoint, GPU1.
- P3-36 bounded: tanh mean / midpoint, GPU0.
- P3-37 control: legacy mean / landing reference, GPU3.
- P3-37 bounded: tanh mean / landing reference, GPU2.

12update×64env integration checks and trace audits passed. Smoke outcome does not select a winner. Main runs evaluate the final frozen checkpoint on64development episodes, archive fixed env0 follow video, and report actual travel time and strict flight counts. Identical-geometry clones do not establish generalization. No final dynamic demo or champion is claimed.
