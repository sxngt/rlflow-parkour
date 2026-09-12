"""Predeclared env3 illustration after its prior success; preserve all64 outcomes."""
from pathlib import Path
import json,subprocess,sys,time
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/'artifacts/p3-65-follow-queue.json'
def main():
 STATE.write_text(json.dumps({'status':'WAITING','selection':'env3 selected from prior P360bridge evaluation success; new execution, not original replay; all64 outcomes retained'})+'\n')
 wait_result('p3-62-clearance__final-evaluation',time.monotonic()+4500)
 out=ROOT/'artifacts/p3-65-bridge-follow-env3'
 subprocess.run([sys.executable,'scripts/run_job.py','--gpu','3','--timeout','360','evaluate','--config','artifacts/p3-60-bridge/config.json','--checkpoint','artifacts/p3-60-bridge/checkpoint-001200.pt','--episodes','64','--diagnostics','--video','--video-camera-mode','follow','--video-follow-env-index','3','--video-selection-reason','Prior P360 bridge evaluation env3 succeeded; explicitly selected illustration in a NEW execution, not an original-state replay. All64 outcomes retained.','--research-tag','phase:P3','--research-tag','step:p3-65-selected-follow-illustration','--out',str(out)],cwd=ROOT,check=True)
 audit=check(out);r=json.loads((out/'evaluation.json').read_text());replay=json.loads((out/'replay.json').read_text())
 assert replay['episode']==r['results'][3] and replay['visible_env_ids']==[3]
 STATE.write_text(json.dumps({'status':'COMPLETED','audit':audit,'followed_episode':r['results'][3],'selection':replay['selection']})+'\n')
if __name__=='__main__':
 try:main()
 except Exception as e:STATE.write_text(json.dumps({'status':'FAILED','error':repr(e)})+'\n');raise
