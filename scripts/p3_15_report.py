"""Report extended-distance capability without reinterpreting gap success."""
import json
from pathlib import Path
from p3_15_evaluate import evaluation_plan
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    rows=[]
    for item in evaluation_plan():
        path=ROOT/item['out'];check(path)
        result=json.loads((path/'evaluation.json').read_text())
        rows.append(dict(seed=item['seed'],suite=item['suite'],out=item['out'],successes=result['successes'],by_distance=result['by_distance']))
    (ROOT/'docs/p3-15-results.json').write_text(json.dumps({'new_training_steps':2*1024*24*800,'evaluations':rows},indent=2)+'\n')
    print(json.dumps(rows,indent=2))
