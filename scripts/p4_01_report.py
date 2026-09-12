"""Audit spatial-friction trials and describe supported foot motion by segment."""
import json
from pathlib import Path
import numpy as np
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def summarize(path, seed, friction):
    audit=check(path)
    run=json.loads((path/'run.json').read_text())
    report=json.loads((path/'evaluation.json').read_text())
    with np.load(path/'motion-trace.npz') as z:a={k:z[k] for k in z.files}
    force=a['force'][...,2];contact=np.zeros_like(force,dtype=bool);state=np.zeros(force.shape[1:],dtype=bool)
    for t in range(len(force)):
        state=np.where(state,force[t]>2,force[t]>5);contact[t]=state
    consecutive=contact[1:]&contact[:-1]&a['valid'][1:,:,None]&a['valid'][:-1,:,None]
    same_segment=a['segment'][1:]==a['segment'][:-1]
    distance=np.linalg.norm(np.diff(a['foot_pos'][...,:2],axis=0),axis=-1)
    segments=[]
    for segment in range(8):
        mask=consecutive&same_segment[:,:,None]&(a['segment'][1:,:,None]==segment)
        total=float((distance*mask).sum());seconds=float(mask.sum()*.005)
        segments.append({'segment':segment,'supported_foot_seconds':seconds,'supported_foot_center_travel_m':total,
                         'supported_motion_m_per_foot_second':total/seconds if seconds else None})
    failures=[r for r in report['results'] if not r['success']]
    return {'run':path.name,'seed':seed,'authored_later_pad_friction':friction,'successes':report['successes'],
            'completed_hops_histogram':report['completed_hops_histogram'],
            'failure_diagnostics':{k:sum(bool(r[k]) for r in failures) for k in ['failure','timeout','nonfoot_collision','launch_in_region','first_touch_all_within','precise_stabilized_once','mapped_contact_ok']},
            'segments':segments,'audit':audit['audit'],'material_contract':run['evaluation_support'].get('friction_variation')}


if __name__=='__main__':
    items=[]
    for seed in (1,2):
        items.append(summarize(ROOT/f'artifacts/p3-11-mapped-seed{seed}-hops8',seed,.5))
        name=f'p4-01-mapped-seed{seed}-friction'+('0.2' if seed==1 else '0p2')
        items.append(summarize(ROOT/'artifacts'/name,seed,.2))
        items.append(summarize(ROOT/f'artifacts/p4-01-mapped-seed{seed}-friction0p05',seed,.05))
    out={'scope':'Supported foot-center movement is not proven slip; unequal survival changes exposure. Authored friction is not measured effective contact friction.', 'evaluations':items}
    (ROOT/'docs/p4-01-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in x.items() if k not in ('segments','material_contract')} for x in items],indent=2))
