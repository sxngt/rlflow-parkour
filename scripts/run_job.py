#!/usr/bin/env python3
"""Single-host bounded worker launcher with UUID selection and a per-GPU lease.

This is a P0 execution wrapper, not the full resource broker or shared-GPU scheduler.
"""
from __future__ import annotations
import argparse
import csv
import fcntl
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from process_group import stop_process_group

ROOT = Path(__file__).resolve().parents[1]


def query_gpus():
    raw = subprocess.check_output(["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"], text=True)
    return {row[1].strip(): int(row[0]) for row in csv.reader(io.StringIO(raw))}


def compute_processes():
    raw = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid,gpu_uuid,used_memory", "--format=csv,noheader"], text=True)
    return [{"pid": int(row[0]), "gpu_uuid": row[1].strip(), "memory_mib": row[2].strip()}
            for row in csv.reader(io.StringIO(raw)) if row]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gpu", required=True, help="GPU UUID, or host index resolved immediately to UUID")
    p.add_argument("--timeout", type=float, default=1800)
    p.add_argument('--skip-final-evaluation', action='store_true', help='Opt out for debug/profiling training runs')
    p.add_argument("--python", default="/mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh")
    p.add_argument("kind", choices=["train", "evaluate", "collision_probe", "support_probe", "support_assignment_probe"])
    p.add_argument("worker_args", nargs=argparse.REMAINDER)
    args = p.parse_args()
    gpus = query_gpus()
    gpu = args.gpu if args.gpu in gpus else next((uuid for uuid, index in gpus.items() if str(index) == args.gpu), None)
    if gpu is None:
        p.error("GPU not found")
    if "--out" not in args.worker_args:
        p.error("worker --out required")
    out = Path(args.worker_args[args.worker_args.index("--out") + 1]).resolve()
    if out.exists():
        p.error("Output already exists; create a new attempt")
    out.parent.mkdir(parents=True, exist_ok=True)
    leases = ROOT / "artifacts" / "leases"
    leases.mkdir(parents=True, exist_ok=True)
    lease = (leases / (gpu + ".lock")).open("a+")
    try:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        p.error("GPU has an active parkour lease")
    existing = compute_processes()
    if any(row["gpu_uuid"] == gpu for row in existing):
        p.error("GPU has an existing compute process")
    child_env = os.environ.copy()
    child_env.update(CUDA_VISIBLE_DEVICES=gpu, PARKOUR_GRAPHICS_GPU=str(gpus[gpu]),
                     OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4", PYTHONUNBUFFERED="1")
    command = [args.python, str(ROOT / "scripts" / (args.kind + ".py")), *args.worker_args]
    log = out.with_suffix(".log").open("x")
    telemetry = out.with_suffix(".gpu.jsonl").open("x")
    started = time.time()
    proc = subprocess.Popen(command, cwd=ROOT, env=child_env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    timed_out = False
    interrupted = False
    observed_pids = set()
    try:
        while proc.poll() is None:
            rows = compute_processes()
            # Worker PID is written before simulator startup; never infer ownership
            # from a GPU being occupied, since other jobs may start concurrently.
            if (out / "run.json").exists():
                try:
                    observed_pids.add(json.loads((out / "run.json").read_text())["pid"])
                except (KeyError, json.JSONDecodeError):
                    pass
            own = [row for row in rows if row["pid"] in observed_pids]
            telemetry.write(json.dumps({"unix_s": time.time(), "worker_gpu_processes": own}) + "\n")
            telemetry.flush()
            if time.time() - started > args.timeout:
                timed_out = True
                break
            time.sleep(2)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        cleanup = stop_process_group(proc)
        time.sleep(1)
        remaining = [row for row in compute_processes() if row["pid"] in observed_pids]
        resource_released = not remaining and not cleanup['remaining_processes']
        # Reconcile a worker killed before it could write a terminal state.
        run_file = out / "run.json"
        run = json.loads(run_file.read_text()) if run_file.exists() else {}
        if run.get("status") == "RUNNING" and (proc.returncode != 0 or timed_out or interrupted):
            run.update(status="CANCELED" if interrupted else "FAILED",
                       supervisor_error="timeout" if timed_out else "worker_exit",
                       finished_unix_s=time.time())
            temporary = run_file.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(run, indent=2) + "\n")
            temporary.replace(run_file)
        result = {"gpu_uuid": gpu, "graphics_host_index": gpus[gpu], "command": command,
                  "exit_code": proc.returncode, "timed_out": timed_out, "interrupted": interrupted,
                  "wall_seconds": time.time() - started, "worker_pids": sorted(observed_pids),
                  "remaining_gpu_processes": remaining, "resource_released": resource_released,
                  "process_cleanup": cleanup,
                  "worker_status": run.get("status", "LOST")}
        out.with_suffix(".supervisor.json").write_text(json.dumps(result, indent=2) + "\n")
        log.close()
        telemetry.close()
        fcntl.flock(lease, fcntl.LOCK_UN)
        lease.close()
    print(json.dumps(result), flush=True)
    if proc.returncode == 0 and run.get('kind') == 'evaluate' and run.get('status') == 'SUCCEEDED' and resource_released and (out/'evaluation.mp4').exists():
        archive = subprocess.run([sys.executable, str(ROOT/'scripts/collect_results.py'), str(out)], cwd=ROOT)
        if archive.returncode:
            print('Evaluation completed, but result/ collection failed; rerun collect_results.py.', file=sys.stderr)
            return 1
    if proc.returncode == 0 and run.get('kind') == 'train' and run.get('status') == 'SUCCEEDED' and resource_released and not args.skip_final_evaluation:
        evaluation_out = out.with_name(out.name + '__final-evaluation')
        command = [sys.executable, str(ROOT/'scripts/run_job.py'), '--gpu', gpu, '--timeout', '180',
                   '--python', args.python, 'evaluate', '--config', str(out/'config.json'),
                   '--checkpoint', str(out/run['checkpoint']['path']), '--out', str(evaluation_out), '--video']
        if run.get('config',{}).get('evaluation_episodes'):
            command.extend(['--episodes',str(run['config']['evaluation_episodes'])])
        if run.get('config',{}).get('evaluation_diagnostics'):
            command.append('--diagnostics')
        for field, flag in [('evaluation_video_envs', '--video-envs'), ('evaluation_camera_side', '--video-camera-side')]:
            if run.get('config', {}).get(field):
                command.extend([flag, str(run['config'][field])])
        evaluation = subprocess.run(command, cwd=ROOT)
        result['final_evaluation'] = {'path': str(evaluation_out), 'exit_code': evaluation.returncode}
        out.with_suffix('.supervisor.json').write_text(json.dumps(result, indent=2)+'\n')
        if evaluation.returncode:
            print('Training succeeded; final evaluation/archive needs attention.', file=sys.stderr)
            return 1
    return 0 if proc.returncode == 0 and run.get("status") == "SUCCEEDED" and resource_released and not timed_out and not interrupted else 1


if __name__ == "__main__":
    sys.exit(main())
