"""Final easy-to-medium curriculum stage versus equal-total-budget direct training."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_discrete_parkour
from parkour.terrain_contract import training_support
STATE=ROOT/'artifacts/p3-68-stage3.json'
def write(d):
 p=STATE.with_suffix('.tmp');p.write_text(json.dumps(d,indent=2)+'\n');p.replace(STATE)
def main():
 write({'status':'WAITING','budget':'2x1200updates; third stage, equal3x1200updates since P351; both now full35cm medium24gaps'})
 deadline=time.monotonic()+5400
 while time.monotonic()<deadline:
  d=json.loads((ROOT/'artifacts/p3-63-continuation.json').read_text())
  if d['status']=='COMPLETED':break
  if d['status']=='FAILED':raise RuntimeError('P363 failed; inspect before scheduling')
  time.sleep(10)
 else:raise TimeoutError('P363')
 r=json.loads((ROOT/'artifacts/p3-63-bridge__final-evaluation/evaluation.json').read_text())
 score=sum(x['completed_surface_transfers'] for x in r['results'])/r['episodes']
 if score<16:raise RuntimeError('Native curriculum advancement gate failed: '+str(score))
 def lane(pair):
  gpu,arm=pair;parent=ROOT/'artifacts'/('p3-63-'+arm)
  c=json.loads((parent/'config.json').read_text());c['iterations']=1200;c['terrain_contract']['layout']=build_discrete_parkour('medium',1,24)
  c['research_tags']=['phase:P3','step:p3-68-full-medium-stage3','condition:'+arm,'purpose:matched-total-budget']
  training_support(c);cfg=ROOT/'artifacts'/('p3-68-'+arm+'-config.json')
  with cfg.open('x') as f:json.dump(c,f,indent=2)
  out=ROOT/'artifacts'/('p3-68-'+arm)
  subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600','train','--config',str(cfg),'--fork-from',str(parent/'checkpoint-001200.pt'),'--out',str(out)],cwd=ROOT,check=True)
  return {'arm':arm,'result':check(Path(str(out)+'__final-evaluation'))}
 write({'status':'TRAINING','native_advancement_score':score,'budget':'1200updates each, both full medium; equal cumulative3x1200updates'})
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,[(0,'bridge'),(2,'direct')]))
 write({'status':'COMPLETED','results':results})
if __name__=='__main__':
 try:main()
 except Exception as e:write({'status':'FAILED','error':repr(e)});raise
