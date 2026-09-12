"""Continue mixed-map learning and test harder geometry with a matched-budget arm."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_mixed_discrete
from parkour.terrain_contract import training_support
from parkour.runtime import atomic_json
from audit_continuous_evaluation import check
STATE=ROOT/'artifacts/p3-72-continuation.json'
def main():
 atomic_json(STATE,{'status':'WAITING','budget':'2 x 1200 updates x 1024 envs; continue25percent vs harder50percent; common parent chosen only by native development success then transfer count; both evaluated at both difficulties'})
 deadline=time.monotonic()+5400
 while time.monotonic()<deadline:
  d=json.loads((ROOT/'artifacts/p3-70-continuation.json').read_text())
  if d['status']=='COMPLETED':break
  if d['status']=='FAILED':raise RuntimeError('P370 requires failure inspection')
  time.sleep(10)
 else:raise TimeoutError('P370 completion')
 scores={}
 for arm in ('control','jitter'):
  p=ROOT/'artifacts'/('p3-70-'+arm+'__final-evaluation');check(p)
  e=json.loads((p/'evaluation.json').read_text())
  scores[arm]=(e['successes'],sum(r['completed_surface_transfers'] for r in e['results'])/e['episodes'])
 winner=max(scores,key=scores.get);parent=ROOT/'artifacts'/('p3-70-'+winner)
 atomic_json(STATE,{'status':'TRAINING','parent':str(parent),'selection_scores':scores,'selection_scope':'Native development evaluations only; seed2 was not used to select parent. No statistical superiority claim.'})
 def lane(pair):
  gpu,arm,fraction=pair;c=json.loads((parent/'config.json').read_text());c['iterations']=1200
  c['terrain_contract']['layout']=build_mixed_discrete(1,fraction)
  c['research_tags']=['phase:P3','step:p3-72-mixed-difficulty','condition:'+arm,'purpose:matched-budget-development']
  training_support(c);config=ROOT/'artifacts'/('p3-72-'+arm+'-config.json')
  with config.open('x') as f:json.dump(c,f,indent=2)
  out=ROOT/'artifacts'/('p3-72-'+arm)
  def run(args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600',*args],cwd=ROOT,check=True)
  run(['train','--config',str(config),'--fork-from',str(parent/'checkpoint-001200.pt'),'--out',str(out)])
  native=check(Path(str(out)+'__final-evaluation'))
  opposite=.5 if fraction==.25 else .25;other=ROOT/'artifacts'/('p3-72-'+arm+'-cross-difficulty')
  run(['evaluate','--config',str(config),'--checkpoint',str(out/'checkpoint-001200.pt'),'--mixed-course-fraction',str(opposite),'--shared-course-seed','1','--episodes','64','--diagnostics','--video','--out',str(other)])
  return {'arm':arm,'training_fraction':fraction,'native':native,'cross_difficulty':check(other)}
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,[(0,'quarter',.25),(2,'half',.5)]))
 atomic_json(STATE,{'status':'COMPLETED','parent':str(parent),'selection_scores':scores,'results':results})
if __name__=='__main__':
 try:main()
 except BaseException as e:atomic_json(STATE,{'status':'FAILED','error':repr(e)});raise
