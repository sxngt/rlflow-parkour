"""Matched-budget speed/progress reward package comparison after P348 release."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,time,sys
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'artifacts/p3-53-comparison-driver.json'
def main():
 STATE.write_text(json.dumps({'status':'WAITING','budget':'2x1200updates; identical checkpoint1700, original vs capped progress/speed-cost20'})+'\n')
 check(wait_result('p3-53-speed-balance-smoke__final-evaluation',time.monotonic()+600))
 def lane(pair):
  gpu,level,kind=pair
  wait_result('p3-48-discrete-'+level+'-resume2400',time.monotonic()+5400)
  check(wait_result('p3-48-discrete-'+level+'-resume2400__final-evaluation',time.monotonic()+900))
  c=json.loads((ROOT/'artifacts/p3-48-discrete-easy-resume2400/config.json').read_text());c['iterations']=1200;c['num_envs']=1024
  if kind=='capped':c['motion_control'].update(version='motion_control_v2',cap_progress_reward=True,speed_cost=20.)
  c['research_tags']=['phase:P3','step:p3-53-speed-progress-balance','condition:'+kind,'purpose:matched-budget-comparison']
  cfg=ROOT/f'artifacts/p3-53-{kind}-config.json'
  with cfg.open('x') as f:json.dump(c,f,indent=2)
  out=ROOT/f'artifacts/p3-53-speed-{kind}'
  subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','3600','train','--config',str(cfg),'--fork-from',str(ROOT/'artifacts/p3-48-discrete-easy-resume2400/checkpoint-001700.pt'),'--out',str(out)],cwd=ROOT,check=True)
  return check(Path(str(out)+'__final-evaluation'))
 with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(lane,[(0,'easy','capped'),(1,'medium','control')]))
 STATE.write_text(json.dumps({'status':'COMPLETED','results':r})+'\n')
if __name__=='__main__':
 try:main()
 except Exception as e:STATE.write_text(json.dumps({'status':'FAILED','error':str(e)})+'\n');raise
