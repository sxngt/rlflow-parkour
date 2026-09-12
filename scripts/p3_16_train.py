"""Bounded reach expansion, followed by real-gap and retention evaluations."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from research_course_history_batch import capacity_gate
from audit_chained_evaluation import check
ROOT=Path(__file__).resolve().parents[1]

def worker(seed):
    source=f'artifacts/p3-16-reach-seed{seed}'
    cmd=[sys.executable,'scripts/run_job.py','--gpu',str(seed-1),'--timeout','2400','train','--config','configs/p3-16-reach-curriculum.json','--seed',str(seed),'--fork-from',f'artifacts/p3-15-longer-seed{seed}/checkpoint-000800.pt','--out',source]
    subprocess.run(cmd,cwd=ROOT,check=True);capacity_gate(Path(source).name,1200)
    metrics=[json.loads(line) for line in (ROOT/source/'metrics.jsonl').read_text().splitlines()]
    for update,high in [(1,.3),(301,.4),(601,.5)]:
        row=metrics[update-1];assert row['train_forward_range_m']==[0.,high]
        if update>1:assert row['curriculum_reset_all']
    results=[]
    for suite in ('full-gap','continuous'):
        out=f'artifacts/p3-16-eval-seed{seed}-{suite}'
        cmd=[sys.executable,'scripts/run_job.py','--gpu',str(seed-1),'--timeout','300','evaluate','--config',source+'/config.json','--checkpoint',source+'/checkpoint-001200.pt','--out',out,'--chain-hops','1','--support-mode',suite,'--support-matched-material','--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json','--episodes','64','--video','--diagnostics','--video-envs','64','--video-camera-side','4','--research-tag','phase:P3','--research-tag','step:p3-16-full-gap-capability','--research-tag','purpose:'+suite]
        if suite=='full-gap':cmd+=['--gap-travel-m','.5']
        else:cmd+=['--evaluation-forward-m','0','.05','.1','.15']
        subprocess.run(cmd,cwd=ROOT,check=True);a=check(ROOT/out)
        results.append(dict(seed=seed,suite=suite,out=out,successes=a['successes'],episodes=a['episodes'],audit='passed'))
    (ROOT/f'docs/p3-16-seed{seed}-results.json').write_text(json.dumps(results,indent=2)+'\n')
    return results

if __name__=='__main__':
    capacity_gate('p3-16-reach-smoke',12,64)
    for seed in (1,2):
        for name in (f'p3-16-reach-seed{seed}',f'p3-16-eval-seed{seed}-full-gap',f'p3-16-eval-seed{seed}-continuous'):
            p=ROOT/'artifacts'/name
            if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(worker,(1,2)))
    (ROOT/'docs/p3-16-results.json').write_text(json.dumps(results,indent=2)+'\n')
