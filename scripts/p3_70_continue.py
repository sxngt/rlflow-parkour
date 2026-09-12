"""Mixed-route training: clean starts versus half bounded pose-jitter starts."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'artifacts/p3-70-continuation.json'
def write(d):
 p=STATE.with_suffix('.tmp');p.write_text(json.dumps(d,indent=2)+'\n');p.replace(STATE)
def main():
 write({'status':'TRAINING','budget':'2x1200updates1024env; sameP363parent; mixed25percent; native and unseen geometry seed2 evaluations with jitter disabled'})
 def lane(pair):
  gpu,arm=pair;check(wait_result('p3-70-'+arm+'-smoke__final-evaluation',time.monotonic()+600))
  def run(args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600',*args],cwd=ROOT,check=True)
  out=ROOT/'artifacts'/('p3-70-'+arm)
  run(['train','--config','configs/p3-70-'+arm+'.json','--fork-from','artifacts/p3-63-bridge/checkpoint-001200.pt','--out',str(out)])
  native=check(Path(str(out)+'__final-evaluation'))
  target=ROOT/'artifacts'/('p3-70-'+arm+'-seed2')
  run(['evaluate','--config',str(out/'config.json'),'--checkpoint',str(out/'checkpoint-001200.pt'),'--mixed-course-fraction','.25','--shared-course-seed','2','--episodes','64','--diagnostics','--video','--out',str(target)])
  return {'arm':arm,'native':native,'unseen_seed2':check(target)}
 with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(lane,[(1,'jitter'),(3,'control')]))
 write({'status':'COMPLETED','results':result})
if __name__=='__main__':
 try:main()
 except Exception as e:write({'status':'FAILED','error':repr(e)});raise
