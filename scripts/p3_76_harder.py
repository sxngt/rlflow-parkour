"""Bounded higher-difficulty continuation and stronger-parent transfer trials."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.shared_terrain import build_mixed_discrete
from parkour.terrain_contract import training_support
from parkour.runtime import atomic_json
from audit_continuous_evaluation import check
STATE=ROOT/'artifacts/p3-76-harder.json'
def main():
 atomic_json(STATE,{'status':'TRAINING','budget':'3 arms x 1800 PPO updates x 1024env; half continuation, half from stronger quarter, three-quarter challenge from stronger quarter'})
 def lane(spec):
  gpu,arm,parent,fraction=spec;parent=ROOT/'artifacts'/parent;check(Path(str(parent)+'__final-evaluation'))
  c=json.loads((parent/'config.json').read_text());c['iterations']=1800;c['terrain_contract']['layout']=build_mixed_discrete(1,fraction)
  c['research_tags']=['phase:P3','step:p3-76-harder-mixed','condition:'+arm,'purpose:higher-difficulty-training']
  training_support(c);cfg=ROOT/'artifacts'/('p3-76-'+arm+'-config.json')
  with cfg.open('x') as f:json.dump(c,f,indent=2)
  out=ROOT/'artifacts'/('p3-76-'+arm)
  def run(args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','5400',*args],cwd=ROOT,check=True)
  run(['train','--config',str(cfg),'--fork-from',str(parent/'checkpoint-001200.pt'),'--out',str(out)])
  native=check(Path(str(out)+'__final-evaluation'))
  regression=ROOT/'artifacts'/('p3-76-'+arm+'-quarter-regression')
  run(['evaluate','--config',str(cfg),'--checkpoint',str(out/'checkpoint-001800.pt'),'--mixed-course-fraction','.25','--shared-course-seed','1','--episodes','64','--diagnostics','--video','--out',str(regression)])
  return {'arm':arm,'native':native,'regression':check(regression)}
 with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(lane,[(0,'half-continue','p3-72-half',.5),(1,'half-strong-parent','p3-72-quarter',.5),(2,'three-quarter','p3-72-quarter',.75)]))
 atomic_json(STATE,{'status':'COMPLETED','results':results})
if __name__=='__main__':
 try:main()
 except BaseException as e:atomic_json(STATE,{'status':'FAILED','error':repr(e)});raise
