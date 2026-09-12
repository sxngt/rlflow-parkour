"""Two bounded longer/harder runs, native audit, and full-medium transfer evaluation."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'artifacts/p3-60-continuation.json'
def write(d):
 p=STATE.with_suffix('.tmp');p.write_text(json.dumps(d,indent=2)+'\n');p.replace(STATE)
def lane(item):
 gpu,arm=item
 smoke=wait_result('p3-60-'+arm+'-smoke__final-evaluation',time.monotonic()+600);check(smoke)
 out=ROOT/('artifacts/p3-60-'+arm)
 subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600','train','--config','configs/p3-60-'+arm+'.json','--fork-from','artifacts/p3-51-discrete-easy/checkpoint-001200.pt','--out',str(out)],cwd=ROOT,check=True)
 native=check(Path(str(out)+'__final-evaluation'))
 transfer=None
 if arm=='bridge':
  target=ROOT/'artifacts/p3-60-bridge-full-medium-transfer'
  subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','360','evaluate','--config',str(out/'config.json'),'--checkpoint',str(out/'checkpoint-001200.pt'),'--shared-course-level','medium','--shared-course-seed','1','--shared-course-transfers','24','--episodes','64','--video','--out',str(target)],cwd=ROOT,check=True)
  transfer=check(target)
 return {'arm':arm,'native':native,'full_medium_transfer':transfer}
def main():
 write({'status':'WAITING_THEN_TRAINING','budget':'two1200update1024env runs; native videos and one full-medium transfer evaluation; no promotion'})
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lane,[(0,'bridge'),(2,'direct')]))
 write({'status':'COMPLETED','results':results})
if __name__=='__main__':
 try:main()
 except Exception as e:write({'status':'FAILED','error':repr(e)});raise
