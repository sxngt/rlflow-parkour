# P3-11: six/eight-hop geometric courses

Fixed P3-08 mapped seed 1/2 checkpoints, each evaluated on six and eight 15cm forward transitions (0.90/1.20m goals), 28/36 finite pads. No new training. Same 64 development initial conditions, mapped_contact_v1, explicit map_envelope_v1, hold-last preparation, 4s per hop. Geometric candidate search uses the expanded horizon; physical state is preserved across every intermediate landing.

Run all four evaluations with independent GPU leases, 64-robot camera-side 4 MP4, 200Hz diagnostics and chained-event audits. Report completed-hop distributions, first failing segment and contract, timings and representative behavior. Additional pads alter geometry; this is not a claim that the trajectory prefix must equal shorter layouts. Repeated horizontal foothold translation is not varied-terrain/high-speed generalization.
