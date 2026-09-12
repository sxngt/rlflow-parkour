"""One infrastructure-only retry, after authoritative zero-step timeout and release."""
import hashlib,json,subprocess,sys
from pathlib import Path
from run_job import compute_processes
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'artifacts/p2-27-continuous-seed2'
new=ROOT/'artifacts/p2-27-continuous-seed2-retry1'
if __name__=='__main__':
    if new.exists() or new.with_suffix('.log').exists():raise RuntimeError('Retry already exists; inspect the existing attempt')
    run=json.loads((old/'run.json').read_text())
    supervisor=json.loads(old.with_suffix('.supervisor.json').read_text())
    assert run['status']=='FAILED' and run.get('supervisor_error')=='timeout'
    assert supervisor['timed_out']
    cleanup=None
    if not supervisor['resource_released']:
        cleanup=json.loads((ROOT/'artifacts/p2-27-seed2-orphan-cleanup.json').read_text())
        assert cleanup['pid']==run['pid'] and cleanup['resource_released'] and cleanup['lease_available']
        assert not cleanup['remaining_gpu_processes']
    else:
        assert not supervisor['remaining_gpu_processes']
    assert not Path(f"/proc/{run['pid']}").exists()
    assert not list(old.glob('checkpoint-*.pt'))
    assert not (old/'metrics.jsonl').exists() or not (old/'metrics.jsonl').read_text().strip()
    assert not any(p['gpu_uuid']==supervisor['gpu_uuid'] for p in compute_processes())
    config=json.loads((old/'config.json').read_text());assert config['seed']==2 and config['iterations']==1600 and config['num_envs']==1024
    manifest={'original_run':old.name,'retry_run':new.name,'reason':'simulator_initialization_timeout_before_first_logged_update','retry_limit':1,'original_recorded_environment_steps':0,'original_supervisor':supervisor,'orphan_cleanup':cleanup,'original_run_sha256':hashlib.sha256((old/'run.json').read_bytes()).hexdigest(),'config_sha256':hashlib.sha256((old/'config.json').read_bytes()).hexdigest(),'resume_checkpoint':None,'contract':'Same seed/config, restart initialization; original failed attempt preserved and its resource time counted separately.'}
    manifest_path=ROOT/'artifacts/p2-27-seed2-recovery.json'
    with manifest_path.open('x') as f:json.dump(manifest,f,indent=2)
    result=subprocess.run([sys.executable,'scripts/run_job.py','--gpu',supervisor['gpu_uuid'],'--timeout','1800','train','--config',str(old/'config.json'),'--out',str(new)],cwd=ROOT)
    sys.exit(result.returncode)
