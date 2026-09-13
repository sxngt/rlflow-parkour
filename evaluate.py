"""RLflow 진입점 (명령서 3.2): python evaluate.py --checkpoint <path> --suite eval_suite/<x>.yaml --out <dir> [--config-name <name>] [overrides]

시나리오마다 scripts/evaluate.py 를 서브프로세스로 실행한다 (고정 개발군 episodes_per_scenario 개, --video).
suite 의 scenario = {name, args: [...scripts/evaluate.py 인자...]} — 예: nominal [], low_friction ["--course-friction", "0.05"].
report.json: env/success_rate, env/ep_return(results[].return 평균), env/ep_len(results[].length 평균), custom/fail_rate, custom/mean_final_error_m.
parkour 평가는 고정 시나리오 집합이므로 per_seed 는 시나리오별 값이다 (seeds = [0]).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from train import ensure_sidecar  # noqa: E402  (sidecar/sha 도우미 재사용)

KEEP = ("evaluation.json", "scenarios.json", "replay.json", "run.json", "config.json", "terrain.json", "first-frame.png", "planner-states.json", "chain-events.json")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--suite", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--config-name", default="config")
    p.add_argument("overrides", nargs="*")
    a = p.parse_args()
    from hydra import compose, initialize_config_dir
    from lab_logging.lineage import collect_lineage
    from omegaconf import OmegaConf

    with initialize_config_dir(config_dir=str(ROOT / "configs"), version_base=None):
        cfg = compose(config_name=a.config_name, overrides=a.overrides)
    config = OmegaConf.to_container(cfg, resolve=True)
    assert isinstance(config, dict)
    for k in ("project", "fork_from", "resume", "smoke", "device", "eval"):
        config.pop(k, None)
    suite_path = ROOT / a.suite
    suite = yaml.safe_load(suite_path.read_text())
    n_ep = int(suite.get("episodes_per_scenario", 64))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ckpt = Path(a.checkpoint)
    ensure_sidecar(ckpt)
    # parkour checkpoint 는 학습 config 를 통째로 담고 있고 read_checkpoint/restore 가 그것과 평가 config 의 일치를 요구한다.
    # 스윕 trial 처럼 override 로 바뀐 값(LR, 탐색 상한, 보상 계수)은 Hydra 로 재구성할 수 없으므로 checkpoint 의 config 를 평가 config 로 쓴다.
    import torch

    saved = torch.load(str(ckpt), map_location="cpu", weights_only=False).get("config")
    if isinstance(saved, dict) and saved.get("task"):
        for k in ("research_tags",):
            saved[k] = config.get(k, saved.get(k))
        print(f"evaluate: using the checkpoint's embedded config (task={saved.get('task')}, iterations={saved.get('iterations')})", flush=True)
        config = saved
    cfg_json = out / "config.json"
    cfg_json.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    per_scn: dict[str, dict[str, float]] = {}
    failure_counts: dict[str, int] = {}
    videos: list[Path] = []
    for scn in suite["scenarios"]:
        name = scn["name"]
        sdir = out / name
        if sdir.exists():
            shutil.rmtree(sdir)
        cmd = [sys.executable, str(ROOT / "scripts" / "evaluate.py"), "--config", str(cfg_json), "--checkpoint", str(ckpt), "--out", str(sdir),
               "--episodes", str(n_ep), "--video", *[str(x) for x in scn.get("args", [])]]
        print("+", " ".join(cmd), flush=True)
        rc = subprocess.run(cmd, cwd=str(ROOT), env={**os.environ, "PARKOUR_GRAPHICS_GPU": os.environ.get("PARKOUR_GRAPHICS_GPU", "0"), "PYTHONUNBUFFERED": "1"}).returncode
        if rc != 0:
            print(f"scenario {name} failed (exit {rc})", file=sys.stderr)
            return rc or 1
        ev = json.loads((sdir / "evaluation.json").read_text())
        results = ev.get("results") or []
        rets = [float(r.get("return", 0.0)) for r in results]
        lens = [float(r.get("length", 0.0)) for r in results]
        m = {"env/success_rate": float(ev.get("success_rate", 0.0)), "env/ep_return": float(np.mean(rets)) if rets else 0.0,
             "env/ep_len": float(np.mean(lens)) if lens else 0.0, "custom/fail_rate": float(ev.get("failure_rate", 0.0)),
             "custom/timeout_rate": float(ev.get("timeout_rate", 0.0)), "custom/mean_final_error_m": float(ev.get("mean_final_error_m") or 0.0)}
        per_scn[name] = m
        for r in results:
            if r.get("failure"):
                reason = next((k[len("failure_"):] for k in ("failure_nonfoot", "failure_outside_map", "failure_low_body", "failure_tilt") if r.get(k)), "failure")
                failure_counts[reason] = failure_counts.get(reason, 0) + 1
        mp4 = sdir / "evaluation.mp4"
        if mp4.exists():
            vdir = out / "videos"
            vdir.mkdir(exist_ok=True)
            v = vdir / f"{name}.mp4"
            shutil.copyfile(mp4, v)
            videos.append(v)
        print(f"  {name}: " + " ".join(f"{k}={v:.3f}" for k, v in m.items()), flush=True)
    names = list(per_scn)
    keys = list(next(iter(per_scn.values())).keys())
    per_seed = {k: [per_scn[s][k] for s in names] for k in keys}      # 시나리오 축을 seed 축으로 (고정 개발군)
    metrics = {k: {"mean": float(np.mean(v)), "std": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0, "per_scenario": {s: per_scn[s][k] for s in names}} for k, v in per_seed.items()}
    lineage = collect_lineage(cfg, ROOT)
    report = {"schema_version": 1, "policy_ref": lineage.policy_ref(), "suite": a.suite, "seeds": [0], "metrics": metrics, "per_seed": per_seed,
              "gate": {**suite.get("gate", {})}, "scenario_defs_hash": hashlib.sha256(suite_path.read_bytes()).hexdigest(), "failure_counts": failure_counts,
              "episodes_per_scenario": n_ep, "scenarios": names}
    (out / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v["mean"] for k, v in metrics.items()}, indent=2))
    if os.environ.get("MLFLOW_RUN_ID"):
        import mlflow

        with mlflow.start_run(run_id=os.environ["MLFLOW_RUN_ID"]):
            mlflow.log_metrics({f"eval/{k.replace('/', '_')}": v["mean"] for k, v in metrics.items()})
            mlflow.log_artifact(str(out / "report.json"), artifact_path=f"eval/{suite_path.stem}")
            mlflow.set_tag("suite", a.suite)
            for name in names:
                for f in KEEP:
                    fp = out / name / f
                    if fp.exists():
                        mlflow.log_artifact(str(fp), artifact_path=f"eval/{suite_path.stem}/{name}")
            for v in videos:
                mlflow.log_artifact(str(v), artifact_path="videos/eval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
