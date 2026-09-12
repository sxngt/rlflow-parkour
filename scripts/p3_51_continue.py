"""Bounded capability-gated curriculum after P348; no automatic promotion."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,time,subprocess,sys
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_discrete_parkour
from parkour.terrain_contract import training_support
STATE=ROOT/'artifacts/p3-51-continuation.json'
def write(d):
 p=STATE.with_suffix('.tmp');p.write_text(json.dumps(d,indent=2)+'\n');p.replace(STATE)
def main():
 write({'status':'WAITING','budget':'two successor runs x1200updates; choose route length from audited progress'})
 deadline=time.monotonic()+5400;data={}
 for level in ('easy','medium'):
  p=wait_result('p3-48-discrete-'+level+'-resume2400',deadline)
  e=wait_result(p.name+'__final-evaluation',deadline);check(e)
  r=json.loads((e/'evaluation.json').read_text())['results']
  data[level]=(p,sum(x['completed_surface_transfers'] for x in r)/len(r))
 plans=[]
 for level,gpu in [('easy',2),('medium',3)]:
  parent,score=data[level]
  if level=='medium' and score<8 and data['easy'][1]>=12:parent,score=data['easy']
  transfers=24 if data[level][1]>=12 else 16
  c=json.loads((parent/'config.json').read_text());c['iterations']=1200
  c['terrain_contract']['layout']=build_discrete_parkour(level,1,transfers)
  c['research_tags']=['phase:P3','step:p3-51-long-discrete-curriculum','difficulty:'+level,'purpose:capability-gated-curriculum']
  training_support(c)
  path=ROOT/f'artifacts/p3-51-{level}-config.json'
  with path.open('x') as f:json.dump(c,f,indent=2)
  checkpoint=parent/json.loads((parent/'run.json').read_text())['checkpoint']['path']
  plans.append({'gpu':gpu,'level':level,'transfers':transfers,'parent':str(checkpoint),'config':str(path),'source_mean_transfers':score})
 write({'status':'TRAINING','plans':plans,'scope':'development curriculum selection; not champion promotion or generalization proof'})
 def lane(plan):
  out=ROOT/f'artifacts/p3-51-discrete-{plan["level"]}'
  subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(plan['gpu']),'--timeout','3600','train','--config',plan['config'],'--fork-from',plan['parent'],'--out',str(out)],cwd=ROOT,check=True)
  return check(Path(str(out)+'__final-evaluation'))
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,plans))
 write({'status':'COMPLETED','plans':plans,'results':results})
if __name__=='__main__':
 try:main()
 except Exception as error:write({'status':'FAILED','error':str(error)});raise
