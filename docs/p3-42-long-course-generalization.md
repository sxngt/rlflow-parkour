# P3-42 — Frozen long-course policy on new geometry

Frozen P340 rise05 checkpoint001600, geometry seed101, easy/medium/hard. Preserve gap scale1.25,60transfers,10gaps,5cm rise per gap, original controller. Development probes; not locked final tests.

| Level | Success | Mean transfers /60 | Mean travel seconds |
|---|---|---|---|
| easy | 0/64 | 59.92 | 10.036 |
| medium | 0/64 | 58.08 | 11.612 |
| hard | 0/64 | 0.00 | 0.265 |

Easy/medium failures concentrate near the terminal section. Hard fails before the first transfer; do not claim difficulty generalization. Artifact hashes, episode IDs and GPU release audits passed. These three diagnostic evaluations did not enable physics trace recording, so no independent physics-rate flight-count audit is claimed. Original fixed-env0 follow videos archived in result.

P343 starts1200-update per-level training on easy/medium seed101 from the same frozen parent,1024parallel environments each. This changes seed101 to an explicit training/development scenario; future generalization must use new seeds. Hard configuration is prepared but NOT launched because the immediate first-transfer failure needs a graded transition. Separate per-level policies are not a single universal controller. Automatic final64episode evaluation and first-robot follow recording remain enabled.
