"""Bounded two-seed course versus deck continuation experiment."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from audit_artifacts import audit
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]


def gate(name, first, updates, envs):
    p=ROOT/'artifacts'/name
    audit(p)
    rows=[json.loads(s) for s in (p/'metrics.jsonl').read_text().splitlines()]
    assert len(rows)==updates and rows[0]['iteration']==first and rows[-1]['iteration']==first+updates-1
    assert all(sum(r['hop_environment_steps'])==envs*24 for r in rows)
    check(p.with_name(p.name+'__final-evaluation'))
    replay=json.loads((p.with_name(p.name+'__final-evaluation')/'replay.json').read_text())
    assert len(replay['visible_env_ids'])==64 and replay['camera']['framing_side']==4
    return {'run':name,'new_steps':updates*envs*24,'updates':updates}


def worker(item):
    mode,seed,gpu=item
    out=f'artifacts/p3-04-{mode}-seed{seed}'
    cmd=[sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','2400','train',
         '--config',f'configs/p3-04-{mode}.json','--seed',str(seed),
         '--fork-from',f'artifacts/p2-40-weighted-seed{seed}/checkpoint-000800.pt','--out',out]
    code=subprocess.run(cmd,cwd=ROOT).returncode
    if code==0:gate(Path(out).name,1,800,1024)
    return {'condition':mode,'seed':seed,'exit_code':code}


if __name__=='__main__':
    gates=[gate('p3-04-course-smoke',1,12,64),gate('p3-04-course-resume',13,2,64),
           gate('p3-04-course-profile',1,60,1024)]
    configs=[json.loads((ROOT/f'configs/p3-04-{m}.json').read_text()) for m in ('course','deck')]
    for c in configs:
        assert c['iterations']==800 and c['num_envs']==1024
        c.pop('research_tags');c['terrain_contract'].pop('mode');c['terrain_contract'].pop('layout')
    assert configs[0]==configs[1]
    plan=[('course',1,0),('deck',1,1),('course',2,2),('deck',2,3)]
    for mode,seed,gpu in plan:
        p=ROOT/f'artifacts/p3-04-{mode}-seed{seed}'
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    (ROOT/'artifacts/p3-04-training-gates.json').write_text(json.dumps(gates,indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,plan))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
