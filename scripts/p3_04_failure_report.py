"""Identify failed hop criteria without equating terminal gates with root causes."""
import json
from pathlib import Path
from audit_chained_evaluation import check
from p3_04_evaluate import evaluation_plan
ROOT=Path(__file__).resolve().parents[1]


def summarize(item):
    p=ROOT/item['out'];check(p)
    events=json.loads((p/'chain-events.json').read_text())
    groups={}
    keys=('success','failure','timeout','valid_flight','launch_in_region','first_touch_all_within',
          'travel_requirement_met','precise_stabilized_once','nonfoot_collision')
    for segment in (0,1):
        rows=[h for h in events['hops'] if h['segment']==segment]
        m=[h['metrics'] for h in rows]
        landed=[r['flight_forward_m'] for r in m if r['flight_touch_recorded']]
        groups[str(segment)]={'attempts':len(rows),'counts':{k:sum(r[k] for r in m) for k in keys},
            'local_steps_min_max':([min(r['local_steps'] for r in rows),max(r['local_steps'] for r in rows)] if rows else None),
            'recorded_flight_distance_min_max_m':([min(landed),max(landed)] if landed else None)}
    return dict(condition=item['condition'],seed=item['seed'],suite=item['suite'],hops=groups)


if __name__=='__main__':
    result={'scope':'development per-hop criterion counts; not exclusive cause labels or proof of causality',
            'results':[summarize(i) for i in evaluation_plan() if i['suite'] in ('course','deck')]}
    (ROOT/'docs/p3-04-failure-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in result['results']:
        if r['suite']=='course':print(r)
