"""Identical explicit evaluation contracts for course/deck candidates and parents."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
from p3_04_train import gate
from audit_artifacts import audit
from audit_chained_evaluation import check

ROOT=Path(__file__).resolve().parents[1]


def evaluation_plan():
    result=[]
    for seed in (1,2):
        for condition in ('parent','mapped','strict'):
            source=f'artifacts/p3-04-course-seed{seed}' if condition=='parent' else f'artifacts/p3-08-{condition}-seed{seed}'
            for suite in ('mapped3','strict2','continuous'):
                out=f'artifacts/p3-08-eval-{condition}-seed{seed}-{suite}'
                command=[sys.executable,'scripts/run_job.py','--gpu',str(len(result)%4),'--timeout','300','evaluate',
                    '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
                    '--chain-hops','1' if suite=='continuous' else ('3' if suite=='mapped3' else '2'),
                    '--support-mode',('continuous' if suite=='continuous' else 'course'),'--support-matched-material',
                    '--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
                    '--episodes','64','--diagnostics','--video','--video-envs','64','--video-camera-side','4',
                    '--research-tag','phase:P3','--research-tag','step:p3-08-course-training',
                    '--research-tag','condition:'+condition,'--research-tag','purpose:'+suite]
                if suite=='continuous':command+=['--evaluation-forward-m','0','.05','.1','.15']
                else:command+=['--chain-settle-mode','hold-last']
                if suite=='mapped3':command+=['--map-goal-forward-m','.45','--mapped-contact-progress']
                if suite=='strict2':command+=['--map-goal-forward-m','.30']
                result.append(dict(seed=seed,condition=condition,suite=suite,source=source,out=out,gpu=len(result)%4,command=command))
    return result


def worker(gpu,plan):
    for item in plan:
        if item['gpu']!=gpu:continue
        code=subprocess.run(item['command'],cwd=ROOT).returncode
        if code:return dict(gpu=gpu,exit_code=code,out=item['out'])
        check(ROOT/item['out'])
    return dict(gpu=gpu,exit_code=0)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true');args=p.parse_args()
    plan=evaluation_plan()
    assert len(plan)==len({p['out'] for p in plan})==18
    if args.dry_run:
        print(json.dumps(plan,indent=2));sys.exit(0)
    for condition in ('mapped','strict'):
        for seed in (1,2):gate(f'p3-08-{condition}-seed{seed}',1,800,1024)
    for seed in (1,2):audit(ROOT/f'artifacts/p3-04-course-seed{seed}')
    for item in plan:
        p=ROOT/item['out']
        if p.exists() or p.with_suffix('.log').exists():raise RuntimeError('Existing attempt '+str(p))
    (ROOT/'artifacts/p3-08-evaluation-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda gpu:worker(gpu,plan),range(4)))
    print(json.dumps(results),flush=True)
    sys.exit(int(any(r['exit_code'] for r in results)))
