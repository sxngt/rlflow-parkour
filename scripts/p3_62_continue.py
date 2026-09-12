"""Bounded matched exploration restart, stronger height-reference versus control."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'artifacts/p3-62-continuation.json'
def lane(pair):
 gpu,arm=pair
 def run(args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600',*args],cwd=ROOT,check=True)
 if arm=='control':
  deadline=time.monotonic()+3600
  while time.monotonic()<deadline:
   path=ROOT/'artifacts/p3-61-collection.json'
   if path.exists():
    state=json.loads(path.read_text())
    if state['status']=='FAILED':raise RuntimeError('Data collection failed; inspect GPU before reuse')
    if state['status']=='COMPLETED':break
   time.sleep(10)
  else:raise TimeoutError('Data collection')
  if not (ROOT/'artifacts/p3-62-control-smoke').exists():run(['train','--config','configs/p3-62-control-smoke.json','--fork-from','artifacts/p3-56-explore/checkpoint-001200.pt','--out','artifacts/p3-62-control-smoke'])
 check(wait_result('p3-62-'+arm+'-smoke__final-evaluation',time.monotonic()+600))
 out=ROOT/'artifacts'/('p3-62-'+arm)
 if not out.exists():run(['train','--config','configs/p3-62-'+arm+'.json','--fork-from','artifacts/p3-56-explore/checkpoint-001200.pt','--out',str(out)])
 return check(wait_result(out.name+'__final-evaluation',time.monotonic()+4500))
def main():
 STATE.write_text(json.dumps({'status':'WAITING_THEN_TRAINING','budget':'2x1200updates,1024env; sameP356explore1200parent; explicit new exploration schedule and fresh optimizer; no promotion'})+'\n')
 with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(lane,[(3,'clearance'),(1,'control')]))
 STATE.write_text(json.dumps({'status':'COMPLETED','results':r})+'\n')
if __name__=='__main__':
 try:main()
 except Exception as e:STATE.write_text(json.dumps({'status':'FAILED','error':repr(e)})+'\n');raise
