"""RLflow 진입점 (명령서 3.3): python export.py --checkpoint <path> --out <dir>/policy.onnx

Kit 없이 동작한다: 체크포인트의 config.runner.policy + state_dict 모양으로 rsl_rl ActorCritic 을 만들고
정규화(EmpiricalNormalization) + actor 를 하나의 모듈로 묶어 배치 1 ONNX 로 내보낸다. io_spec.json 은 관측 차원과 12 관절 토크.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

CONTROL_HZ = 50.0


class Policy(torch.nn.Module):
    def __init__(self, normalizer: torch.nn.Module, actor: torch.nn.Module):
        super().__init__()
        self.normalizer, self.actor = normalizer, actor

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.actor(self.normalizer(obs))


def build(data: dict) -> tuple[Policy, int, int]:
    from rsl_rl.modules import ActorCritic, EmpiricalNormalization

    config = data["config"]
    pcfg = dict(config["runner"]["policy"])
    pcfg.pop("class_name", None)
    state = data["model"]
    actor_keys = sorted((k for k in state if k.startswith("actor.") and k.endswith(".weight")), key=lambda k: int(k.split(".")[1]))
    num_obs = int(state[actor_keys[0]].shape[1])
    num_actions = int(state[actor_keys[-1]].shape[0])
    ac = ActorCritic(num_obs, num_obs, num_actions, **{k: v for k, v in pcfg.items() if k in ("actor_hidden_dims", "critic_hidden_dims", "activation", "init_noise_std")})
    missing, unexpected = ac.load_state_dict(state, strict=False)
    bad = [k for k in missing if k.startswith("actor.")]
    if bad:
        raise RuntimeError(f"actor weights missing: {bad}")
    if unexpected:
        print(f"note: ignored checkpoint keys {unexpected} (exploration cap 등 학습 전용)")
    norm: torch.nn.Module = EmpiricalNormalization(shape=[num_obs], until=int(1e8))
    try:
        norm.load_state_dict(data["normalizer"])
    except Exception as e:  # noqa: BLE001
        try:
            from parkour.observation_history import HistoryNormalization

            norm = HistoryNormalization(config, num_obs)          # type: ignore[call-arg]
            norm.load_state_dict(data["normalizer"])
        except Exception:  # noqa: BLE001
            raise RuntimeError(f"normalizer state incompatible: {e}") from e
    return Policy(norm, ac.actor).eval(), num_obs, num_actions


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--config-name", default="config")
    p.add_argument("overrides", nargs="*")
    a = p.parse_args()
    data = torch.load(a.checkpoint, map_location="cpu", weights_only=False)
    policy, num_obs, num_actions = build(data)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    x = torch.zeros(1, num_obs)
    torch.onnx.export(policy, x, str(out), input_names=["obs"], output_names=["actions"], opset_version=17, dynamo=False)
    import onnxruntime as ort

    sess = ort.InferenceSession(str(out), providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(0)
    for _ in range(3):
        xi = rng.standard_normal((1, num_obs)).astype(np.float32)
        got = sess.run(None, {"obs": xi})[0]
        with torch.no_grad():
            ref = policy(torch.from_numpy(xi)).numpy()
        assert np.allclose(ref, got, atol=1e-4), f"onnx mismatch {np.abs(ref - got).max()}"
    config = data["config"]
    io_spec = {
        "schema_version": 1,
        "obs": [{"name": "policy", "dim": num_obs, "unit": "mixed", "offset": [0.0] * num_obs, "scale": [1.0] * num_obs}],
        "action": {"name": "joint_target", "dim": num_actions, "unit": "rad", "offset": [0.0] * num_actions, "scale": [1.0] * num_actions},
        "control_hz": float(config.get("control_hz", CONTROL_HZ)),
        "history_len": 1,
        "task": config.get("task"),
        "observation_history": config.get("observation_history"),
    }
    (out.parent / "io_spec.json").write_text(json.dumps(io_spec, indent=2))
    print(f"exported {out} ({out.stat().st_size} bytes) obs={num_obs} actions={num_actions} + io_spec.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
