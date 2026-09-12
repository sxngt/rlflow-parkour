"""Bounded continuation: audited motion adaptation -> disjoint terrain training.

No model promotion. At most two 1200-update successor runs. Existing GPU leases
remain authoritative. Errors stop the lane and are recorded, never retried forever.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
from audit_continuous_evaluation import check
from audit_artifacts import audit
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'artifacts/p3-46-continuation.json'

def write(data):
    temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(STATE)

def wait_result(name,deadline):
    folder=ROOT/'artifacts'/name
    while time.monotonic()<deadline:
        supervisor=folder.with_suffix('.supervisor.json')
        if supervisor.exists():
            record=json.loads(supervisor.read_text())
            if record['exit_code']!=0 or not record.get('resource_released'):raise RuntimeError('Failed worker: '+name)
            audit(folder);return folder
        time.sleep(10)
    raise TimeoutError(name)

def main():
    write({'status':'WAITING','budget':'two successor runs x1200updates x1024env; no automatic promotion'})
    deadline=time.monotonic()+5400
    candidates=[]
    for kind in ('rate8','rate12'):
        train=wait_result('p3-46-'+kind+'-train',deadline)
        evaluation=wait_result(train.name+'__final-evaluation',deadline);check(evaluation)
        report=json.loads((evaluation/'evaluation.json').read_text());rows=report['results']
        score=(report['successes'],sum(r['completed_surface_transfers'] for r in rows)/len(rows))
        candidates.append((score,train))
    score,parent=max(candidates,key=lambda item:item[0])
    if score[1]<3:
        write({'status':'NEEDS_REVIEW','reason':'Neither constrained policy reached mean three transfers; no blind harder training','scores':[(x,str(y)) for x,y in candidates]});return
    for kind in ('discrete-easy','discrete-medium'):
        pilot=wait_result('p3-46-'+kind+'-train',deadline)
        check(wait_result(pilot.name+'__final-evaluation',deadline))
    config=json.loads((parent/'config.json').read_text());checkpoint=parent/json.loads((parent/'run.json').read_text())['checkpoint']['path']
    write({'status':'TRAINING_SUCCESSORS','parent':str(parent),'selection':'development success count then mean transfers; not champion','score':score})
    def lane(pair):
        gpu,level=pair
        target=json.loads((ROOT/f'configs/p3-46-discrete-{level}.json').read_text())
        child=dict(config);child['terrain_contract']=target['terrain_contract'];child['iterations']=1200
        child['research_tags']=['phase:P3','step:p3-47-constrained-transfer','difficulty:'+level,'purpose:curriculum-transfer']
        path=ROOT/f'artifacts/p3-47-{level}-config.json'
        with path.open('x') as f:json.dump(child,f,indent=2)
        out=ROOT/f'artifacts/p3-47-constrained-discrete-{level}'
        subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600','train','--config',str(path),'--fork-from',str(checkpoint),'--out',str(out)],cwd=ROOT,check=True)
        audit(out);return check(Path(str(out)+'__final-evaluation'))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,[(2,'easy'),(3,'medium')]))
    write({'status':'COMPLETED','results':results,'next':'Review actual speed, motion limits, first-gap execution and four-step planner before further budget'})
if __name__=='__main__':
    try:main()
    except Exception as error:
        write({'status':'FAILED','error':str(error)});raise
