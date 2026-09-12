"""Summarize matched spatial-friction training and retention outcomes."""
import json
from pathlib import Path
from p4_02_evaluate import evaluation_plan
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    rows=[]
    for item in evaluation_plan():
        path=ROOT/item['out'];check(path)
        report=json.loads((path/'evaluation.json').read_text())
        rows.append({k:item[k] for k in ('seed','condition','suite','source','out')})
        rows[-1].update(successes=report['successes'],episodes=report['episodes'],completed_hops_histogram=report['completed_hops_histogram'])
    (ROOT/'docs/p4-02-comparison.json').write_text(json.dumps({'new_training_steps':4*800*1024*24,'evaluations':rows},indent=2)+'\n')
    lines=['# P4-02 matched final evaluations','','| Condition | Seed | Uniform eight-hop | Friction 0.2 | Friction 0.05 | Continuous regression |','|---|---:|---:|---:|---:|---:|']
    for condition in ('lowfriction','control'):
        for seed in (1,2):
            r={x['suite']:x for x in rows if x['condition']==condition and x['seed']==seed}
            lines.append('| '+condition+' | '+str(seed)+' | '+' | '.join(str(r[s]['successes'])+'/64' for s in ('uniform8','friction0p2','friction0p05','continuous'))+' |')
    lines+=['','Fixed development scenarios; two trained seeds per condition. Course uses mapped_contact_v1/map_envelope_v1; continuous regression uses its separate original single-hop criterion. No champion promotion implied. Authored material friction is not measured effective robot-pad friction.']
    (ROOT/'docs/p4-02-comparison.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
