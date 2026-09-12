"""Matched spatial-friction versus unchanged-material continuation training."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from p3_04_train import gate
ROOT=Path(__file__).resolve().parents[1]


def worker(item):
    condition,seed,gpu=item
    cmd=[sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','2400','train',
         '--config',f'configs/p4-02-{condition}.json','--seed',str(seed),
         '--fork-from',f'artifacts/p3-08-mapped-seed{seed}/checkpoint-000800.pt',
         '--out',f'artifacts/p4-02-{condition}-seed{seed}']
    code=subprocess.run(cmd,cwd=ROOT).returncode
    if code==0:gate(f'p4-02-{condition}-seed{seed}',1,800,1024)
    return {'condition':condition,'seed':seed,'exit_code':code}


if __name__=='__main__':
    gates=[gate('p4-02-lowfriction-smoke',1,12,64),gate('p4-02-lowfriction-resume',13,2,64)]
    a=json.loads((ROOT/'configs/p4-02-lowfriction.json').read_text());b=json.loads((ROOT/'configs/p4-02-control.json').read_text())
    for c in (a,b):
        assert c['iterations']==800 and c['num_envs']==1024
        c.pop('research_tags');c['terrain_contract'].pop('surface_material_overrides');c['terrain_contract'].pop('friction_variation')
    assert a==b
    plan=[('lowfriction',1,0),('control',1,1),('lowfriction',2,2),('control',2,3)]
    for condition,seed,gpu in plan:
        p=ROOT/f'artifacts/p4-02-{condition}-seed{seed}'
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    (ROOT/'artifacts/p4-02-training-gates.json').write_text(json.dumps(gates,indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(worker,plan))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
