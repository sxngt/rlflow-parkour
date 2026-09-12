"""Common reach and regression evaluation plan for P3-15 capability models."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
def evaluation_plan():
    result=[]
    for seed in (1,2):
        source=f'artifacts/p3-15-longer-seed{seed}'
        for suite in ('reach','continuous'):
            out=f'artifacts/p3-15-eval-seed{seed}-{suite}'
            cmd=[sys.executable,'scripts/run_job.py','--gpu','0','--timeout','300','evaluate',
                 '--config',source+'/config.json','--checkpoint',source+'/checkpoint-000800.pt','--out',out,
                 '--chain-hops','1','--support-mode','deck' if suite=='reach' else 'continuous',
                 '--support-matched-material','--support-calibration','artifacts/p2-11-curriculum-seed0__final-evaluation/run.json',
                 '--evaluation-forward-m',*(['.15','.20','.25','.30'] if suite=='reach' else ['0','.05','.1','.15']),
                 '--episodes','64','--video','--diagnostics','--video-envs','64','--video-camera-side','4',
                 '--research-tag','phase:P3','--research-tag','step:p3-15-longer-jump-training','--research-tag','purpose:'+suite]
            result.append(dict(source=source,out=out,seed=seed,suite=suite,command=cmd))
    return result
