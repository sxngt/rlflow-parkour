"""Extend only the progressing, audited P3-25 pilots to their strict-radius stage."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,subprocess,sys,time
from audit_continuous_evaluation import check
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]
def worker(seed,gpu):
    source=ROOT/f'artifacts/p3-25-either-foot-seed{seed}-pilot800'
    evaluation=source.with_name(source.name+'__final-evaluation')
    deadline=time.monotonic()+2400
    while time.monotonic()<deadline:
        sup=evaluation.with_suffix('.supervisor.json')
        if sup.exists():
            s=json.loads(sup.read_text())
            if s['exit_code']!=0:raise RuntimeError('Pilot evaluation failed')
            if s.get('resource_released'):break
        time.sleep(10)
    else:raise TimeoutError('Pilot did not finish')
    audit(source);check(evaluation)
    rows=[json.loads(s) for s in (source/'metrics.jsonl').read_text().splitlines()]
    assert rows[-1]['iteration']==800 and len(rows)==800
    progress=max(r['live_mean_front_accepted_index'] for r in rows[-100:])
    if progress<1:
        result={'seed':seed,'extended':False,'reason':'No first-surface progress in recent updates','recent_max_live_front_index':progress}
    else:
        time.sleep(3)
        out=f'artifacts/p3-25-either-foot-seed{seed}-continued2400'
        subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600','train',
            '--config','configs/p3-25-either-foot-progression.json','--seed',str(seed),'--iterations','1600',
            '--resume',str(source/'checkpoint-000800.pt'),'--out',out],cwd=ROOT,check=True)
        audit(ROOT/out);result={'seed':seed,'extended':True,'recent_max_live_front_index':progress,
            **check(ROOT/(out+'__final-evaluation'))}
        end=json.loads((ROOT/out/'metrics.jsonl').read_text().splitlines()[-1]);assert end['iteration']==2400
    (ROOT/f'docs/p3-25-seed{seed}-continuation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True);return result
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda pair:worker(*pair),[(1,1),(2,3)]))
    (ROOT/'docs/p3-25-continuation-results.json').write_text(json.dumps(results,indent=2)+'\n')
