"""Bounded fixed-Tracker data collection on three new easy-map seeds."""
from pathlib import Path
import json,subprocess,sys,time
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
from export_planner_dataset import export
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'artifacts/p3-61-collection.json'
def run(args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu','1','--timeout','360',*args],cwd=ROOT,check=True)
def main():
 STATE.write_text(json.dumps({'status':'RUNNING','budget':'3mapseeds,64episodes each; up to4airborne contexts per map,9candidates x8replicas; one fixed checkpoint'})+'\n')
 sources=[]
 for seed in (2,3,101):
  name='p3-61-r2-easy-seed'+str(seed);folder=ROOT/'artifacts'/name
  run(['evaluate','--config','artifacts/p3-51-discrete-easy/config.json','--checkpoint','artifacts/p3-51-discrete-easy/checkpoint-001200.pt','--shared-course-level','easy','--shared-course-seed',str(seed),'--shared-course-transfers','24','--episodes','64','--diagnostics','--video','--out',str(folder)])
  check(folder);states=json.loads((folder/'planner-states.json').read_text())['states']
  for index in range(len(states)):
   out=ROOT/'artifacts'/('p3-61-r2-seed'+str(seed)+'-air'+str(index))
   run(['planner_rollout_probe','--source',str(folder),'--snapshot-index',str(index),'--lean','--out',str(out)]);sources.append(out)
 result=export(sources,ROOT/'artifacts/p3-61-r2-feasibility-dataset')
 STATE.write_text(json.dumps({'status':'COMPLETED','dataset':result})+'\n')
if __name__=='__main__':
 try:main()
 except Exception as e:STATE.write_text(json.dumps({'status':'FAILED','error':repr(e)})+'\n');raise
