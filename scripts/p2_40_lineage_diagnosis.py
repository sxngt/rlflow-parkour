"""Same-scenario single-hop lineage diagnostics, retaining every training seed."""
import json
from pathlib import Path
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]

def build():
    result=[]
    for seed in range(4):
        scenarios=None
        for prefix in ('p2-31-mixed','p2-38-continuous','p2-39-coverage','p2-40-weighted'):
            path=ROOT/f'artifacts/{prefix}-seed{seed}-regression'
            audit(path)
            scene=json.loads((path/'scenarios.json').read_text())['episodes']
            if scenarios is None:scenarios=scene
            assert scenarios==scene
            report=json.loads((path/'evaluation.json').read_text())
            groups=[]
            for goal in (0.,.05,.1,.15):
                rows=[r for r in report['results'] if abs(r['goal_forward_m']-goal)<1e-6]
                assert len(rows)==16
                flights=[r['flight_forward_m'] for r in rows if r['flight_touch_recorded']]
                flags=('launch_in_region','distance_requirement_met','first_touch_all_within','final_all_feet_in_radius','stabilized_once')
                groups.append(dict(goal_m=goal,successes=sum(r['success'] for r in rows),
                    terminal_false_counts={k:sum(not r[k] for r in rows) for k in flags},
                    recorded_flights=len(flights),flight_min_m=min(flights) if flights else None,
                    flight_max_m=max(flights) if flights else None))
            result.append(dict(seed=seed,source=prefix,evaluation=str(path.relative_to(ROOT)),groups=groups))
    return dict(scope='same single-hop continuous scenarios; terminal flags can overlap; lineage association is not causal attribution',records=result)

if __name__=='__main__':
    r=build();(ROOT/'docs/p2-40-lineage-diagnosis.json').write_text(json.dumps(r,indent=2)+'\n')
    for v in r['records']:print(v['seed'],v['source'],[g['successes'] for g in v['groups']])
