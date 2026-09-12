"""Second matched-budget stage: discrete terrain curriculum versus direct medium."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
from audit_continuous_evaluation import check
from p3_46_continue import wait_result
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_discrete_parkour
from parkour.terrain_contract import training_support
STATE=ROOT/'artifacts/p3-63-continuation.json'
def write(d):
 p=STATE.with_suffix('.tmp');p.write_text(json.dumps(d,indent=2)+'\n');p.replace(STATE)
def main():
 write({'status':'WAITING','budget':'two1200update1024env stage2 runs; cumulative2x1200 per arm since P351, fresh optimizer both; full-medium evaluation after each'})
 deadline=time.monotonic()+5400
 while time.monotonic()<deadline:
  status=json.loads((ROOT/'artifacts/p3-60-continuation.json').read_text())
  if status['status']=='FAILED':raise RuntimeError('P360 failed; inspect before scheduling')
  if status['status']=='COMPLETED':break
  time.sleep(10)
 else:raise TimeoutError('P360')
 report=json.loads((ROOT/'artifacts/p3-60-bridge__final-evaluation/evaluation.json').read_text())
 mean=sum(r['completed_surface_transfers'] for r in report['results'])/report['episodes']
 if mean<16:raise RuntimeError('Curriculum advancement gate not met: mean transfers '+str(mean))
 def lane(pair):
  gpu,arm=pair;parent=ROOT/'artifacts'/('p3-60-'+arm)
  c=json.loads((parent/'config.json').read_text());c['iterations']=1200
  if arm=='bridge':c['terrain_contract']['layout']=build_discrete_parkour('medium',1,24,.75)
  c['research_tags']=['phase:P3','step:p3-63-discrete-curriculum-stage2','condition:'+arm,'purpose:matched-total-budget']
  training_support(c);cfg=ROOT/'artifacts'/('p3-63-'+arm+'-config.json')
  with cfg.open('x') as f:json.dump(c,f,indent=2)
  out=ROOT/'artifacts'/('p3-63-'+arm)
  def run(a):subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600',*a],cwd=ROOT,check=True)
  run(['train','--config',str(cfg),'--fork-from',str(parent/'checkpoint-001200.pt'),'--out',str(out)])
  native=check(Path(str(out)+'__final-evaluation'));full=native
  if arm=='bridge':
   fullout=ROOT/'artifacts/p3-63-bridge-full-medium'
   run(['evaluate','--config',str(cfg),'--checkpoint',str(out/'checkpoint-001200.pt'),'--shared-course-level','medium','--shared-course-seed','1','--shared-course-transfers','24','--episodes','64','--diagnostics','--video','--out',str(fullout)])
   full=check(fullout)
  return {'arm':arm,'native':native,'full_medium':full}
 write({'status':'TRAINING','bridge_source_mean_transfers':mean,'budget':'1200updates per arm,2ndstage; equal cumulative environment steps'})
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,[(0,'bridge'),(2,'direct')]))
 write({'status':'COMPLETED','results':results})
if __name__=='__main__':
 try:main()
 except Exception as e:write({'status':'FAILED','error':repr(e)});raise
