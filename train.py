"""RLflow 진입점 (명령서 3.1): python train.py --config-name <name> [overrides] --run-id <mlflow_run_id>

연구 코드(scripts/train.py, src/parkour)는 건드리지 않고 감싼다.
  1) Hydra 로 configs/<name>.yaml 을 조립 → JSON 으로 저장 (기존 트레이너 입력 형식)
  2) scripts/train.py 를 서브프로세스로 실행 (Kit 은 그 안에서 뜬다). 서브프로세스는 os._exit 로 끝나므로 종료 코드가 보존된다.
  3) attempt/metrics.jsonl 을 실시간으로 읽어 계약 지표 이름으로 LabRun 에 기록
  4) 체크포인트 checkpoint-NNNNNN.pt → $CKPT_DIR/step_<env_steps>.pt (+ sidecar) 로 복사·업로드, 마지막을 final 로 표시

지표 매핑 (parkour metrics.jsonl → 계약):
  losses.value_function → train/loss_value, losses.surrogate → train/loss_policy, losses.entropy → train/entropy
  train/kl → 0 (rsl_rl PPO 가 노출하지 않음)
  successes/episodes → custom/success_rate, mean_final_error_m → custom/mean_final_error_m, 그 밖의 숫자 키 → custom/<key>
  env/ep_return → 0 (트레이너가 iteration 단위 return 을 기록하지 않는다 — 자리 채움, 태그 contract_note 참고)
  env/ep_len → terminal_mean_episode_seconds × 50 Hz (있을 때), 없으면 0
  sys/steps_per_s → (환경 스텝 증가분) / wall_seconds
config 추가 키 (선택): fork_from / resume = 체크포인트 경로 또는 "mlflow://<run_id>/checkpoints/step_<n>.pt"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

CONTROL_HZ = 50.0            # sim 200 Hz × decimation 4 (evaluation results[].length 과 episode 초의 비율)
DROP_KEYS = {"project", "fork_from", "resume", "smoke"}


def _split_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--run-id")
    p.add_argument("--distill-from")
    ns, rest = p.parse_known_args(argv)
    if ns.distill_from:
        print("parkour does not support --distill-from", file=sys.stderr)
        sys.exit(3)
    return ns, rest


ARGS, HYDRA_ARGV = _split_args(sys.argv[1:])
sys.argv = [sys.argv[0], *HYDRA_ARGV]

import hydra  # noqa: E402
from lab_logging import LabRun, RecordConfig  # noqa: E402
from lab_logging.checkpoint import ckpt_dir, latest_checkpoint  # noqa: E402
from omegaconf import DictConfig, OmegaConf  # noqa: E402

REC = RecordConfig.from_env()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_sidecar(ckpt: Path) -> dict:
    """parkour read_checkpoint 는 <ckpt>.json {sha256, bytes, completed_iterations, total_environment_steps} 를 요구한다."""
    side = ckpt.with_suffix(".json")
    if side.exists():
        return json.loads(side.read_text())
    import torch

    data = torch.load(ckpt, map_location="cpu", weights_only=False)
    meta = {"sha256": sha256(ckpt), "bytes": ckpt.stat().st_size, "completed_iterations": int(data["completed_iterations"]),
            "total_environment_steps": int(data["total_environment_steps"])}
    side.write_text(json.dumps(meta, indent=2))
    return meta


def resolve_checkpoint(ref: str, dst: Path) -> Path:
    """로컬 경로 또는 mlflow://<run_id>/<artifact path> → 로컬 파일 (+sidecar)."""
    if ref.startswith("mlflow://"):
        import mlflow

        run_id, _, art = ref[len("mlflow://"):].partition("/")
        p = Path(mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=art, dst_path=str(dst)))
        side = art + ".json"
        try:
            mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=side, dst_path=str(dst))
        except Exception:  # noqa: BLE001
            pass
    else:
        p = Path(ref)
    if not p.exists():
        raise FileNotFoundError(f"checkpoint not found: {ref}")
    ensure_sidecar(p)
    return p


def to_metrics(d: dict, prev_steps: int, episode_seconds: float) -> tuple[int, dict[str, float]]:
    step = int(d.get("total_environment_steps", 0))
    losses = d.get("losses") or {}
    m: dict[str, float] = {
        "train/loss_value": float(losses.get("value_function", float("nan"))),
        "train/loss_policy": float(losses.get("surrogate", float("nan"))),
        "train/entropy": float(losses.get("entropy", float("nan"))),
        "train/kl": 0.0,
        "env/ep_return": 0.0,
    }
    if d.get("terminal_mean_episode_seconds") is not None:
        m["env/ep_len"] = float(d["terminal_mean_episode_seconds"]) * CONTROL_HZ
    else:
        m["env/ep_len"] = 0.0
    wall = float(d.get("wall_seconds") or 0.0)
    m["sys/steps_per_s"] = (step - prev_steps) / wall if wall > 0 and step > prev_steps else float("nan")
    eps = int(d.get("episodes") or 0)
    if eps > 0:
        m["custom/success_rate"] = float(d.get("successes", 0)) / eps
        m["custom/failure_rate"] = float(d.get("failures", 0)) / eps
    for k, v in d.items():
        if k in ("iteration", "total_environment_steps", "wall_seconds", "losses") or not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        name = "custom/" + "".join(c if c.isalnum() else "_" for c in k.lower()).strip("_")
        m.setdefault(name, float(v))
    return step, m


def stream_metrics(proc: subprocess.Popen, metrics_file: Path, run: LabRun, episode_seconds: float) -> int:
    """metrics.jsonl 을 꼬리 추적하며 LabRun 에 기록. 마지막 스텝을 돌려준다."""
    pos, buf, prev_steps, last_step = 0, "", 0, 0
    while True:
        alive = proc.poll() is None
        if metrics_file.exists():
            with metrics_file.open() as f:
                f.seek(pos)
                chunk = f.read()
                pos = f.tell()
            buf += chunk
            lines = buf.split("\n")
            buf = lines.pop()          # 미완성 마지막 줄 보류
            for line in lines:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                step, m = to_metrics(d, prev_steps, episode_seconds)
                if step > 0:
                    run.log(step, m)
                    prev_steps, last_step = step, step
        if not alive:
            return last_step
        time.sleep(2.0)


def collect_checkpoints(attempt: Path, run: LabRun) -> Path | None:
    out_dir = ckpt_dir()
    final: tuple[int, Path] | None = None
    for ck in sorted(attempt.glob("checkpoint-*.pt")):
        side = ck.with_suffix(".json")
        if not side.exists():
            continue
        meta = json.loads(side.read_text())
        step = int(meta["total_environment_steps"])
        if step <= 0:
            continue
        dst = out_dir / f"step_{step}.pt"
        if not dst.exists():
            shutil.copyfile(ck, dst)
            shutil.copyfile(side, dst.with_suffix(".json"))
        run.log_checkpoint(dst, step, upload=True)
        if final is None or step > final[0]:
            final = (step, dst)
    return final[1] if final else None


@hydra.main(config_path="configs", config_name="config", version_base=None)
def main(cfg: DictConfig) -> None:
    import mlflow

    config = OmegaConf.to_container(cfg, resolve=True)
    assert isinstance(config, dict)
    smoke = bool(config.pop("smoke", False))
    if str(config.get("device", "cuda:0")).startswith("cpu"):
        print("parkour: device=cpu (dry_run) 미지원 — Isaac Sim 은 GPU 가 필요하다. iterations 를 줄여 GPU 1 로 제출", file=sys.stderr)
        sys.exit(3)
    config.pop("device", None)
    fork_from, resume_ref = config.pop("fork_from", None), config.pop("resume", None)
    for k in DROP_KEYS:
        config.pop(k, None)
    if smoke:
        config["iterations"], config["num_envs"] = min(int(config["iterations"]), 12), min(int(config["num_envs"]), 64)
    work = ckpt_dir()
    attempt = work / "attempt"
    cfg_json = work / "config.json"
    cfg_json.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    with LabRun(cfg, run_id=ARGS.run_id, repo_root=ROOT, template="parkour", robot=f"sim:isaaclab:a1:{config['task']}") as run:
        mlflow.set_tags({"contract_note": "env/ep_return=0 placeholder (parkour trainer logs no per-iteration return); see custom/*", "task": str(config["task"]),
                         "research_tags": ",".join(config.get("research_tags") or [])})
        cmd = [sys.executable, str(ROOT / "scripts" / "train.py"), "--config", str(cfg_json), "--out", str(attempt)]
        resumed = latest_checkpoint(work)
        if attempt.exists():
            # 재시도(선점·노드 장애): 이전 attempt 는 이름을 바꿔 두고 최신 체크포인트에서 재개
            attempt.rename(work / f"attempt-{int(time.time())}")
        if resumed:
            step, path = resumed
            ensure_sidecar(path)
            cmd += ["--resume", str(path)]
            print(f"resume from {path} (env step {step})")
        elif resume_ref:
            cmd += ["--resume", str(resolve_checkpoint(str(resume_ref), work / "init"))]
        elif fork_from:
            cmd += ["--fork-from", str(resolve_checkpoint(str(fork_from), work / "init"))]
        if REC.enabled and REC.train_every_steps > 0:
            cmd.append("--video")
        env = {**os.environ, "PARKOUR_GRAPHICS_GPU": os.environ.get("PARKOUR_GRAPHICS_GPU", "0"), "PYTHONUNBUFFERED": "1"}
        print("+", " ".join(cmd), flush=True)
        proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env)
        last_step = stream_metrics(proc, attempt / "metrics.jsonl", run, float(config.get("episode_seconds", 0.0)))
        rc = proc.returncode
        final = collect_checkpoints(attempt, run)
        for name in ("run.json", "config.json", "metrics.jsonl", "terrain.json", "support-assignment.json", "support-inspection.json", "collision-contract.json"):
            f = attempt / name
            if f.exists():
                mlflow.log_artifact(str(f), artifact_path="parkour")
        video = attempt / "parallel-training.mp4"
        if video.exists() and last_step:
            vdst = work / "videos" / f"step_{last_step}.mp4"
            vdst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(video, vdst)
            run.log_video(vdst, "train")
        if rc != 0:
            raise RuntimeError(f"scripts/train.py exited with {rc} (see attempt/run.json)")
        if final is None:
            raise RuntimeError("no checkpoint produced")
        run.mark_final_checkpoint(final)
        print(f"done: global_step={last_step} ckpt={final}")


if __name__ == "__main__":
    main()
