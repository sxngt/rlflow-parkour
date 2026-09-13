"""Check recorded active-candidate goals survive third-person state playback."""
from pathlib import Path
import subprocess,sys,json,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.runtime import atomic_json,sha256
STATE=ROOT/'artifacts/p3-78-playback.json'
def main():
 atomic_json(STATE,{'status':'RUNNING','scope':'One fixed initial candidate replay validation, not an online planning performance comparison'})
 def run(kind,args):subprocess.run([sys.executable,'scripts/run_job.py','--gpu','3','--timeout','600',kind,*args],cwd=ROOT,check=True)
 run('pipelined_planner_probe',['--role','executor','--source','artifacts/p3-70-control__final-evaluation','--fixed-initial-plan','artifacts/p3-75-mailbox/phase-00.json','--mailbox','artifacts/p3-78-mailbox','--out','artifacts/p3-78-executor'])
 run('render_online_probe',['--source','artifacts/p3-78-executor','--out','artifacts/p3-78-playback'])
 source=ROOT/'artifacts/p3-78-executor';rendered=ROOT/'artifacts/p3-78-playback'
 trace=json.loads((source/'state-playback.json').read_text())['frames'];replay=json.loads((rendered/'replay.json').read_text())
 for actual,frame in zip(trace[::2],replay['trace']):
  assert actual['planned_contacts']==frame['planned_contacts']
 assert len(trace[::2])==len(replay['trace'])
 out=ROOT/'result/P3-78_실행중기록한4스텝빨간발접점_3인칭상태재생';out.mkdir()
 meta=json.loads((rendered/'run.json').read_text())
 for name in ['evaluation.mp4','replay.json','first-frame.png']:
  assert sha256(rendered/name)==meta['artifacts'][name];shutil.copy2(rendered/name,out/name)
 (out/'README.md').write_text('# 기록된 계획 접점 · 빨간 점 · 상태 재생\n\n[영상](evaluation.mp4). 실행 중 승인된 초기 후보8의 다음 네 접촉 목표를 기록하고 후속 렌더링에서 그대로 표시했습니다. 매 프레임 목표 데이터 일치를 검사했습니다. 고정 초기 계획 실행 검증이며 온라인 재계획 성능 비교나 원본 카메라 영상이 아닙니다.\n')
 atomic_json(STATE,{'status':'COMPLETED','verified_frames':len(replay['trace']),'scope':'Recorded active goals equal rendered goals in every frame'})
if __name__=='__main__':
 try:main()
 except BaseException as e:atomic_json(STATE,{'status':'FAILED','error':repr(e)});raise
