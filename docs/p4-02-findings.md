# P4-02: material continuation results and limits

All four800-update runs, native evaluations and16 common evaluations completed and passed artifact/event audits. New training78,643,200 environment steps, roughly770 seconds per run on four concurrent GPUs. Full table: p4-02-comparison.md/json.

At authored later-pad0.2, low-friction training scores33/64 and19/64; equal-budget unchanged-material controls score52/64 and1/64. Mean scores are therefore similar, with opposite seed-specific effects. A blanket claim that low-friction training improves0.2 robustness is not supported. At0.05, low-friction seed1 achieves27/64 while the other three models score0; this is a promising seed-specific result, not reproducible across both seeds.

Uniform eight-hop performance is39/64,63/64 for low-friction versus60/64,64/64 controls. Continuous0/5/10/15cm regression totals16/64,39/64 versus46/64,32/64. Retention remains unresolved and no model is promoted to champion.

Next contact comparison P4-03 adds short history versus a zero-history input control under identical dimensions, initialization and low-friction budget. This tests additional temporal information rather than changing reward coefficients. Separately P3 geometry work continues with height variation and longer airborne reach; the full project does not wait for every minor condition to become perfect.
