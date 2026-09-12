"""Full-horizon online planning on the stronger 24-gap Tracker, plus fixed-plan control."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'artifacts/p3-66-integration.json'
SOURCE='artifacts/p3-60-bridge__final-evaluation'
def wait_state(path):
 deadline=time.monotonic()+5400
 while time.monotonic()<deadline:
  p=ROOT/path
  if p.exists():
   d=json.loads(p.read_text())
   if d['status']=='COMPLETED':return
   if d['status']=='FAILED':raise RuntimeError(str(path)+' failed; resource ownership requires inspection')
  time.sleep(10)
 raise TimeoutError(str(path))
def run(gpu,kind,args):
 subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','360',kind,*args],cwd=ROOT,check=True)
def main():
 STATE.write_text(json.dumps({'status':'WAITING','budget':'one full-horizon online episode and one fixed-plan control on same checkpoint/map, separate state-playback videos'})+'\n')
 wait_state('artifacts/p3-62-continuation.json');wait_state('artifacts/p3-65-follow-queue.json')
 STATE.write_text(json.dumps({'status':'RUNNING','source':SOURCE})+'\n')
 mailbox='artifacts/p3-66-mailbox'
 def planner():run(1,'online_planner_probe',['--role','planner','--threads','1','--full-horizon','--source',SOURCE,'--mailbox',mailbox,'--out','artifacts/p3-66-planner'])
 def execute():run(3,'online_planner_probe',['--role','executor','--threads','1','--lead-steps','225','--source',SOURCE,'--mailbox',mailbox,'--out','artifacts/p3-66-executor'])
 with ThreadPoolExecutor(max_workers=2) as pool:
  a=pool.submit(planner);b=pool.submit(execute);b.result();a.result()
 with ThreadPoolExecutor(max_workers=2) as pool:
  a=pool.submit(run,1,'online_planner_probe',['--role','executor','--fixed-plan','--threads','1','--source',SOURCE,'--mailbox','artifacts/p3-66-control-mailbox','--out','artifacts/p3-66-control'])
  b=pool.submit(run,3,'render_online_probe',['--source','artifacts/p3-66-executor','--out','artifacts/p3-66-online-playback']);a.result();b.result()
 run(3,'render_online_probe',['--source','artifacts/p3-66-control','--out','artifacts/p3-66-control-playback'])
 reports={}
 for arm,source in [('online','p3-66-executor'),('control','p3-66-control')]:
  report=json.loads((ROOT/'artifacts'/source/'execution.json').read_text());reports[arm]=report
  rendered=ROOT/'artifacts'/('p3-66-'+arm+'-playback');runmeta=json.loads((rendered/'run.json').read_text())
  out=ROOT/'result'/('P3-66_26.5cm갭_24구간_'+arm+'_네착지물리계획_상태재생');out.mkdir(exist_ok=False)
  for name in ('evaluation.mp4','replay.json','first-frame.png'):
   assert hashlib.sha256((rendered/name).read_bytes()).hexdigest()==runmeta['artifacts'][name];shutil.copy2(rendered/name,out/name)
  (out/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
  (out/'README.md').write_text('# P3-66 · '+arm+' · 24개 갭\n\n[추적 영상](evaluation.mp4) · [실행 결과](execution.json)\n\n고정된 단일 개발 episode입니다. 영상은 기록 상태의 후속 렌더링입니다. 온라인 조건은 4.5초 뒤 상태를 예측해 네 착지까지 검증한 목표를 적용하며, 빠른 반응이나 통계적 성능 개선이 검증된 것은 아닙니다. 성공 여부는 실행 결과를 그대로 표시합니다.\n')
 STATE.write_text(json.dumps({'status':'COMPLETED','reports':reports})+'\n')
if __name__=='__main__':
 try:main()
 except Exception as e:STATE.write_text(json.dumps({'status':'FAILED','error':repr(e)})+'\n');raise
