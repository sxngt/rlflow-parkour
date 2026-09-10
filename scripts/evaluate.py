"""Fixed, complete first-episode evaluation, with optional original-frame MP4."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parkour.runtime import begin_run, finish_run, launch_app, atomic_json, sha256
from parkour.scenarios import development_scenarios


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/t0-ppo.json"))
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--baseline", choices=["zero", "policy", "shuffled-target"], default="policy")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--episodes", type=int, default=64)
    p.add_argument("--video", action="store_true")
    args = p.parse_args()
    if args.baseline != "zero" and not args.checkpoint:
        p.error("policy evaluation requires checkpoint")
    config = json.loads(args.config.read_text())
    manifest = development_scenarios(args.episodes, config["target_offset_m"])
    config["num_envs"] = args.episodes
    config["seed"] = 10000
    meta = begin_run(args.out, config, "evaluate")
    writer = None
    try:
        launch_app(args.video)
        import numpy as np
        import torch
        from parkour.learning import make_env, make_algorithm, read_checkpoint, restore
        torch.manual_seed(10000)
        env = make_env(config)
        alg, norm = make_algorithm(config, env)
        if args.checkpoint:
            data = read_checkpoint(args.checkpoint)
            restore(data, config, alg, norm, env, training=False)
            meta["checkpoint"] = {"path": str(args.checkpoint.resolve()), "sha256": sha256(args.checkpoint)}
        alg.policy.eval()
        norm.eval()
        env.reset()
        offsets = torch.tensor([episode["foot_offsets_xy_m"] for episode in manifest["episodes"]], device=env.device)
        env.targets[:, :, :2] = env.scene.env_origins[:, None, :2] + env.nominal_xy + offsets
        atomic_json(args.out / "scenarios.json", manifest)
        meta["scenario_sha256"] = sha256(args.out / "scenarios.json")
        meta["baseline"] = args.baseline
        meta["nominal_foot_xy_m"] = env.nominal_xy.tolist()
        initial_targets = env.targets.clone()
        raw = env._get_observations()["policy"]
        done = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        records = [None] * env.num_envs
        trace = []
        frames = 0
        if args.video:
            import imageio.v2 as imageio
            from isaaclab.markers import VisualizationMarkers
            from isaaclab.markers.config import RAY_CASTER_MARKER_CFG
            markers = VisualizationMarkers(RAY_CASTER_MARKER_CFG.replace(prim_path="/World/TargetMarkers"))
            markers.visualize(translations=env.targets.reshape(-1, 3))
            env.render_mode = "rgb_array"
            env.cfg.viewer.resolution = (640, 480)
            origin = env.scene.env_origins[0].cpu().numpy()
            env.sim.set_camera_view(origin + np.array([1.4, 1.4, 1.0]), origin + np.array([0, 0, 0.25]))
            for _ in range(40):
                env.render()
            writer = imageio.get_writer(str(args.out / "evaluation.mp4"), fps=25, codec="libx264")
        with torch.inference_mode():
            for step in range(env.max_episode_length + 1):
                if args.baseline == "zero":
                    action = torch.zeros(env.num_envs, 12, device=env.device)
                else:
                    policy_obs = raw.clone()
                    if args.baseline == "shuffled-target":
                        # Replace only target channels; the true task/reward remains unchanged.
                        policy_obs[:, 45:57] = torch.roll(policy_obs[:, 45:57], 1, dims=0)
                    action = alg.policy.act_inference(norm(policy_obs))
                if args.video and not bool(done[0]):
                    if step % 2 == 0:
                        frame = env.render()
                        if frames == 0:
                            if frame.max() == 0:
                                raise RuntimeError("Black renderer output")
                            imageio.imwrite(args.out / "first-frame.png", frame)
                        writer.append_data(frame)
                        frames += 1
                    trace.append({"sim_time_s": step * env.step_dt,
                        "root_state_w": env.robot.data.root_state_w[0].tolist(),
                        "foot_positions_w": env.robot.data.body_pos_w[0, env.foot_ids].tolist(),
                        "targets_w": initial_targets[0].tolist(), "actions": action[0].tolist()})
                raw_dict, _, term, trunc, extras = env.step(action)
                raw = raw_dict["policy"]
                newly_done = (term | trunc) & ~done
                for index in newly_done.nonzero().flatten().tolist():
                    metrics = extras["terminal_metrics"]
                    records[index] = {"scenario_id": manifest["episodes"][index]["id"],
                        **{key: val[index].item() for key, val in metrics.items()}}
                done |= newly_done
                if bool(done.all()):
                    break
        if not bool(done.all()) or any(record is None for record in records):
            raise RuntimeError("Evaluation incomplete; missing scenario results")
        if writer:
            writer.close()
            writer = None
            atomic_json(args.out / "replay.json", {"artifact_type": "original_simulation_frames",
                "episode": records[0], "fps": 25, "frame_count": frames,
                "video_start_sim_time_s": 0.0, "frame_dt_s": 0.04, "trace": trace})
        count = len(records)
        successes = sum(row["success"] for row in records)
        rate = successes / count
        # Wilson interval describes episode sampling only, not independent training seeds.
        z = 1.96
        center = (rate + z*z/(2*count)) / (1 + z*z/count)
        half = z * ((rate*(1-rate)/count + z*z/(4*count*count))**0.5) / (1 + z*z/count)
        report = {"split": "development", "episodes": count, "successes": successes,
                  "success_rate": rate, "success_wilson95": [center-half, center+half],
                  "failure_rate": sum(row["failure"] for row in records) / count,
                  "timeout_rate": sum(row["timeout"] for row in records) / count,
                  "mean_final_error_m": sum(row["final_error_m"] for row in records) / count,
                  "mean_episode_seconds": sum(row["length"] for row in records) * env.step_dt / count,
                  "results": records}
        atomic_json(args.out / "evaluation.json", report)
        meta["evaluation"] = {key: value for key, value in report.items() if key != "results"}
        meta["artifacts"] = {file.name: sha256(file) for file in args.out.iterdir()
                             if file.suffix in (".mp4", ".png") or file.name in ("evaluation.json", "scenarios.json", "replay.json")}
        finish_run(args.out, meta)
    except BaseException as exc:
        if writer:
            writer.close()
        traceback.print_exc()
        finish_run(args.out, meta, exc)


if __name__ == "__main__":
    main()
