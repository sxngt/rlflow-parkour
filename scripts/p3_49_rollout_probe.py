"""Queue physical candidate tests after P347 releases its GPUs."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys,subprocess,time,json
from p3_46_continue import wait_result
from audit_continuous_evaluation import check
ROOT=Path(__file__).resolve().parents[1]
def lane(level,gpu):
    deadline=time.monotonic()+3600
    predecessor='p3-47-constrained-discrete-'+level
    wait_result(predecessor,deadline);check(wait_result(predecessor+'__final-evaluation',deadline))
    # Evaluate a fixed, already available per-terrain pilot, not a selected lucky episode.
    parent=ROOT/f'artifacts/p3-46-discrete-{level}-train'
    out=ROOT/f'artifacts/p3-49-four-step-candidates-{level}'
    subprocess.run([sys.executable,'scripts/run_job.py','--gpu',str(gpu),'--timeout','900','evaluate',
        '--config',str(parent/'config.json'),'--checkpoint',str(parent/'checkpoint-000600.pt'),
        '--out',str(out),'--episodes','72','--four-step-candidate-probe','--diagnostics','--video','--video-camera-mode','follow',
        '--research-tag','phase:P3','--research-tag','step:p3-49-physical-candidates'],cwd=ROOT,check=True)
    check(out)
    return json.loads((out/'candidate-rollouts.json').read_text())
if __name__=='__main__':
    state=ROOT/'artifacts/p3-49-probe-driver.json'
    state.write_text(json.dumps({'status':'WAITING','budget':'two72episode candidate evaluations'})+'\n')
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda pair:lane(*pair),[('easy',2),('medium',3)]))
        state.write_text(json.dumps({'status':'COMPLETED','results':results},indent=2)+'\n')
    except Exception as error:
        state.write_text(json.dumps({'status':'FAILED','error':str(error)})+'\n');raise
