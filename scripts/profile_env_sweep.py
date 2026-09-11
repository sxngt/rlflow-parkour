#!/usr/bin/env python3
"""Sequential bounded PPO runs with sampled host/GPU telemetry (psutil required)."""
import argparse
import csv
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import psutil

ROOT = Path(__file__).resolve().parents[1]


def sample(proc, out):
    row = {'unix_s': time.time(), 'sample_period_s': 2}
    try:
        raw = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu', '--format=csv,noheader,nounits'], text=True, timeout=5)
        row['gpus'] = [dict(zip(['index','uuid','utilization_pct','memory_mib','total_memory_mib','power_w','temperature_c'], [v.strip() for v in r])) for r in csv.reader(raw.splitlines())]
    except (subprocess.SubprocessError, OSError) as e:
        row['gpu_error'] = str(e)
    row['host'] = {'cpu_times': psutil.cpu_times()._asdict(), 'memory': psutil.virtual_memory()._asdict(), 'disk_io': psutil.disk_io_counters()._asdict(), 'disk_free_bytes': psutil.disk_usage(ROOT).free}
    row['processes'] = []
    try:
        children = psutil.Process(proc.pid).children(recursive=True)
    except psutil.Error:
        children = []
    for p in children:
        try:
            row['processes'].append({'pid':p.pid,'created':p.create_time(),'cpu_times':p.cpu_times()._asdict(),'rss_bytes':p.memory_info().rss,'io':p.io_counters()._asdict()})
        except psutil.Error:
            pass
    try:
        run = json.loads((out/'run.json').read_text())
        row['training_status'] = run['status']
        row['training_iteration'] = run.get('last_iteration',0)
    except (OSError, ValueError, KeyError):
        row['training_status'] = 'STARTING'
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu',default='0')
    parser.add_argument('--sizes',nargs='+',type=int,default=[1024,2048,4096,8192])
    args=parser.parse_args()
    for size in args.sizes:
        config=ROOT/f'configs/profiling/env-{size}.json'
        out=ROOT/f'artifacts/gpu-env-sweep-n{size}-solo'
        if not config.exists() or out.exists():
            raise ValueError(f'Missing config or existing output: {out}')
        telemetry=out.with_suffix('.host-profile.jsonl')
        with telemetry.open('x') as f:
            command=[sys.executable,str(ROOT/'scripts/run_job.py'),'--gpu',args.gpu,'--timeout','600','train','--config',str(config),'--out',str(out),'--seed','0']
            proc=subprocess.Popen(command,cwd=ROOT,start_new_session=True)
            try:
                while proc.poll() is None:
                    f.write(json.dumps(sample(proc,out),allow_nan=False)+'\n');f.flush();time.sleep(2)
            finally:
                if proc.poll() is None:
                    os.killpg(proc.pid,signal.SIGINT)
                    proc.wait(timeout=30)
        print(json.dumps({'size':size,'exit_code':proc.returncode,'profile':str(telemetry)}),flush=True)
        if proc.returncode:
            raise RuntimeError(f'Profile failed at {size}; inspect before proceeding')

if __name__=='__main__':main()
