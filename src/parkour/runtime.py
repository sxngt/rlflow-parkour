"""Run metadata, content hashes, and process-local persistence."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import time


def sha256(path):
    with open(path, "rb") as stream:
        result = hashlib.file_digest(stream, "sha256") if hasattr(hashlib, "file_digest") else None
        if result is not None:
            return result.hexdigest()
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
        return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    tmp.replace(path)


def begin_run(out, config, kind):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    sources = {str(p.relative_to(root)): sha256(p) for folder in ("src", "scripts", "configs")
               for p in (root / folder).rglob("*") if p.is_file() and "__pycache__" not in str(p)}
    for name in sources:
        destination = out / "source-snapshot" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, destination)
    atomic_json(out / "config.json", config)
    revision = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=root, capture_output=True, text=True)
    meta = {
        "schema_version": 1, "status": "RUNNING", "kind": kind, "pid": os.getpid(),
        "started_unix_s": time.time(), "config": config, "research_tags": config.get("research_tags", []), "source_hashes": sources,
        "gpu_uuid": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "physics_device": "cuda:0", "graphics_host_index": os.environ.get("PARKOUR_GRAPHICS_GPU"),
        "git_commit": revision.stdout.strip() if revision.returncode == 0 else None,
    }
    atomic_json(out / "run.json", meta)
    return meta


def finish_run(out, meta, error=None):
    meta["status"] = "FAILED" if error else "SUCCEEDED"
    meta["finished_unix_s"] = time.time()
    meta["shutdown"] = "dedicated_worker_process_exit"
    if error:
        meta["error"] = repr(error)
    atomic_json(Path(out) / "run.json", meta)
    sys.stdout.flush()
    sys.stderr.flush()
    # Isaac Sim 4.5 plugin teardown hangs on this host. No in-memory work may
    # remain here. The supervisor verifies process death and actual GPU release.
    os._exit(1 if error else 0)


def launch_app(video=False):
    from isaaclab.app import AppLauncher
    graphics = int(os.environ.get("PARKOUR_GRAPHICS_GPU", "0"))
    return AppLauncher(headless=True, device="cuda:0", enable_cameras=video,
        multi_gpu=False, kit_args=f"--/renderer/activeGpu={graphics} --/renderer/multiGpu/enabled=false --/renderer/multiGpu/autoEnable=false").app
