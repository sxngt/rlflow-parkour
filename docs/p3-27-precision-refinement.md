# P3-27 — Refinement after long-course progression

P3-25 seed1 update1000 strict16episode evaluation reached two surface transfers then nonfoot collision (all16). No fullcourse or measured jumps. Its continuing training still has large action standard deviations (~.36–.5) while contact radius tightens.

New800update1024env fork from seed1 update1200: copy policy/critic/normalization, fresh optimizer/RNG/curriculum, same robot/action/reward/geometry/seed. Start8cm radius,6cm at400. Std cap .35→.25→.18→.12 at0/200/400/600, floor unchanged. P3-25 uninterrupted continuation remains the engineering reference. This is not an isolated noise ablation because optimizer/curriculum are also restarted; assess strict task KPIs and retain parent lineage. No champion promotion is implied.
