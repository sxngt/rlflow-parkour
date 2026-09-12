"""Bounded six-train/twenty-evaluation queue with per-worker GPU leases.

Training has priority; available workers backfill completed models' evaluations.
This is a persistent-artifact batch runner, not a general resource broker.
"""
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
from audit_artifacts import audit
from audit_chained_evaluation import check
from p3_04_train import gate
from p4_03_evaluate import evaluation_plan as history_evaluations
from p3_15_evaluate import evaluation_plan as reach_evaluations
ROOT=Path(__file__).resolve().parents[1]

def capacity_gate(name,updates=800,envs=1024):
    path=ROOT/'artifacts'/name;audit(path);audit(path.with_name(name+'__final-evaluation'))
    rows=[json.loads(line) for line in (path/'metrics.jsonl').read_text().splitlines()]
    assert len(rows)==updates and rows[0]['iteration']==1 and rows[-1]['iteration']==updates
    assert rows[-1]['total_environment_steps']==updates*envs*24

if __name__=='__main__':
    gate('p4-03-history-smoke',1,12,64);gate('p4-03-history-resume',13,2,64)
    capacity_gate('p3-15-longer-smoke',12,64)
    configs=[json.loads((ROOT/f'configs/p4-03-{condition}.json').read_text()) for condition in ('history','zero')]
    for config in configs:
        assert config['num_envs']==1024 and config['iterations']==800
        config.pop('research_tags');config['observation_history'].pop('mode')
    assert configs[0]==configs[1]
    training=[('p3-15-longer',1),('p3-15-longer',2),('p4-03-history',1),('p4-03-zero',1),('p4-03-history',2),('p4-03-zero',2)]
    evaluations=history_evaluations()+reach_evaluations()
    planned=[]
    for name,seed in training:
        out=f'artifacts/{name}-seed{seed}'
        command=[sys.executable,'scripts/run_job.py','--gpu','0','--timeout','2400','train','--config',f'configs/{name}.json',
                 '--seed',str(seed),'--fork-from',f'artifacts/p3-08-mapped-seed{seed}/checkpoint-000800.pt','--out',out]
        planned.append(dict(kind='train',out=out,command=command))
    planned += [dict(item,kind='evaluate') for item in evaluations]
    for item in planned:
        path=ROOT/item['out']
        if path.exists() or path.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(path))
    (ROOT/'artifacts/course-history-batch-plan.json').write_text(json.dumps(planned,indent=2)+'\n')
    tasks=queue.PriorityQueue();sequence=itertools.count();results=[];lock=threading.Lock();failed=threading.Event()
    for item in planned[:6]:tasks.put((0,next(sequence),item))
    def worker(gpu):
        while True:
            priority,index,item=tasks.get()
            if item is None:tasks.task_done();return
            try:
                if failed.is_set():
                    result=dict(out=item['out'],gpu=gpu,status='not_started_after_batch_failure')
                else:
                    command=list(item['command']);command[command.index('--gpu')+1]=str(gpu)
                    code=subprocess.run(command,cwd=ROOT).returncode
                    if code:raise RuntimeError('worker exit '+str(code))
                    if item['kind']=='train':
                        name=Path(item['out']).name
                        if name.startswith('p3-15'):capacity_gate(name)
                        else:gate(name,1,800,1024)
                        for evaluation in evaluations:
                            if evaluation['source']==item['out']:
                                tasks.put((1,next(sequence),dict(evaluation,kind='evaluate')))
                    else:check(ROOT/item['out'])
                    result=dict(out=item['out'],gpu=gpu,status='succeeded')
            except Exception as error:
                failed.set();result=dict(out=item['out'],gpu=gpu,status='failed',error=str(error))
            finally:
                with lock:
                    results.append(result)
                    state=ROOT/'artifacts/course-history-batch-state.json'
                    temp=state.with_suffix('.tmp');temp.write_text(json.dumps(results,indent=2)+'\n');temp.replace(state)
                    print(json.dumps(result),flush=True)
                tasks.task_done()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(worker,gpu) for gpu in range(4)]
        tasks.join()
        for _ in range(4):tasks.put((99,next(sequence),None))
        for future in futures:future.result()
    if failed.is_set():sys.exit(1)
    assert len(results)==26
    for script in ('p4_03_report.py','p3_15_report.py'):
        code=subprocess.run([sys.executable,'scripts/'+script],cwd=ROOT).returncode
        if code:sys.exit(code)
