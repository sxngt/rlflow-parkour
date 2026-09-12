"""Fresh two-seed long-course pilot with single-robot follow evaluations."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess,sys
from audit_artifacts import audit
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
def worker(seed):
    out=f'artifacts/p3-19-long-easy-seed{seed}'
    subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(seed-1),'--timeout','3600','train',
        '--config','configs/p3-19-long-easy.json','--seed',str(seed),'--out',out],cwd=ROOT,check=True)
    audit(ROOT/out);checked=check(ROOT/(out+'__final-evaluation'))
    metrics=[json.loads(s) for s in (ROOT/out/'metrics.jsonl').read_text().splitlines()]
    assert len(metrics)==3000 and metrics[-1]['total_environment_steps']==3000*1024*24
    report=dict(seed=seed,source=out,**checked)
    replay=json.loads((ROOT/(out+'__final-evaluation')/'replay.json').read_text());assert replay['layout']=='third_person_follow' and replay['visible_env_ids']==[0]
    (ROOT/f'docs/p3-19-seed{seed}-results.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
if __name__=='__main__':
    name='p3-19-long-learning-smoke-retry1'
    audit(ROOT/'artifacts'/name);check(ROOT/'artifacts'/(name+'__final-evaluation'))
    for seed in (1,2):
        path=ROOT/f'artifacts/p3-19-long-easy-seed{seed}'
        if path.exists() or path.with_suffix('.log').exists():raise RuntimeError('Existing attempt')
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,(1,2)))
    (ROOT/'docs/p3-19-results.json').write_text(json.dumps(results,indent=2)+'\n')
