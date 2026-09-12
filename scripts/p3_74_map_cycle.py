"""Bounded sequential map curriculum versus equal-budget single-map training.

Not a simultaneous heterogeneous-environment sampler. Each stage is a new fork,
with the same optimizer-reset boundaries in both arms. Seed2/3 become training;
seed4 is evaluated only after all stages and is not used for model selection.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_mixed_discrete
from parkour.terrain_contract import training_support
from parkour.runtime import atomic_json
from audit_continuous_evaluation import check
STATE=ROOT/'artifacts/p3-74-map-cycle.json'
def main():
 atomic_json(STATE,{'status':'WAITING','budget':'2 arms x 3 stages x 600 PPO updates x 1024env; same P370 control parent; seed1-only vs seed2,3,1 sequence; final fixed seed1,2,3,4 evaluations'})
 deadline=time.monotonic()+3600
 while time.monotonic()<deadline:
  p=ROOT/'artifacts/p3-73-integration.json';d=json.loads(p.read_text())
  if d['status']=='COMPLETED':break
  if d['status']=='FAILED':raise RuntimeError('P373 resource ownership requires inspection')
  time.sleep(10)
 else:raise TimeoutError('P373 completion')
 check(ROOT/'artifacts/p3-70-control__final-evaluation')
 atomic_json(STATE,{'status':'TRAINING','budget':'1800 updates per arm, same 3 optimizer-reset boundaries; seed4 untouched by training'})
 def lane(pair):
  gpu,arm,seeds=pair;parent=ROOT/'artifacts/p3-70-control/checkpoint-001200.pt';stages=[]
  def run(args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600',*args],cwd=ROOT,check=True)
  for stage,seed in enumerate(seeds,1):
   c=json.loads((ROOT/'artifacts/p3-70-control/config.json').read_text());c['iterations']=600
   c['terrain_contract']['geometry_seed']=seed;c['terrain_contract']['layout']=build_mixed_discrete(seed,.25)
   c['research_tags']=['phase:P3','step:p3-74-map-generalization','condition:'+arm,'stage:'+str(stage),'purpose:matched-budget-map-curriculum']
   training_support(c);cfg=ROOT/'artifacts'/('p3-74-'+arm+'-stage'+str(stage)+'-config.json')
   with cfg.open('x') as f:json.dump(c,f,indent=2)
   out=ROOT/'artifacts'/('p3-74-'+arm+'-stage'+str(stage))
   run(['train','--config',str(cfg),'--fork-from',str(parent),'--out',str(out)])
   stages.append(check(Path(str(out)+'__final-evaluation')));parent=out/'checkpoint-000600.pt'
  evaluations=[]
  for seed in (2,3,4):
   target=ROOT/'artifacts'/('p3-74-'+arm+'-final-seed'+str(seed))
   run(['evaluate','--config',str(cfg),'--checkpoint',str(parent),'--mixed-course-fraction','.25','--shared-course-seed',str(seed),'--episodes','64','--diagnostics','--video','--out',str(target)])
   evaluations.append(check(target))
  return {'arm':arm,'training_geometry_seeds':seeds,'stages':stages,'final_evaluations':evaluations}
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,[(1,'single',[1,1,1]),(3,'cycle',[2,3,1])]))
 atomic_json(STATE,{'status':'COMPLETED','results':results})
if __name__=='__main__':
 try:main()
 except BaseException as e:atomic_json(STATE,{'status':'FAILED','error':repr(e)});raise
