"""Bounded A1 physics/contact smoke using an existing Isaac Lab installation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import threading
import time


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "configs/a1-smoke.json")
    parser.add_argument("--video", action="store_true")
    from isaaclab.app import AppLauncher
    AppLauncher.add_app_launcher_args(parser)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    if cfg["steps"] <= 0 or cfg["physics_dt_s"] <= 0:
        raise ValueError("steps and physics_dt_s must be positive")
    args.out.mkdir(parents=True, exist_ok=False)
    metadata = {
        "status": "RUNNING", "config": cfg,
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "device": args.device, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "artifact_type": "original_simulation_frames" if args.video else "state_trace",
        "started_unix_s": time.time(),
    }
    save_json(args.out / "run.json", metadata)
    app = None
    writer = None
    try:
        metadata["gpu_inventory"] = subprocess.check_output([
            "nvidia-smi", "--query-gpu=uuid,name,pci.bus_id,driver_version", "--format=csv"
        ], text=True)
        args.enable_cameras = args.video
        args.kit_args = (getattr(args, "kit_args", "") or "") + (
            " --/renderer/multiGpu/enabled=false --/renderer/multiGpu/autoEnable=false"
        )
        app = AppLauncher(args, multi_gpu=False).app
        import numpy as np
        import torch
        import isaaclab.sim as sim_utils
        from isaaclab.assets import Articulation
        from isaaclab.sensors import ContactSensor, ContactSensorCfg, Camera, CameraCfg
        from isaaclab_assets import UNITREE_A1_CFG

        torch.manual_seed(0)
        metadata["versions"] = {}
        for package in ("torch", "numpy", "isaaclab", "rsl-rl-lib"):
            try:
                metadata["versions"][package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                metadata["versions"][package] = None
        sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=cfg["physics_dt_s"], device=args.device))
        ground = sim_utils.GroundPlaneCfg()
        ground.func("/World/Ground", ground)
        light = sim_utils.DomeLightCfg(intensity=2500.0)
        light.func("/World/Light", light)
        robot_cfg = UNITREE_A1_CFG.copy()
        robot_cfg.prim_path = "/World/Robot"
        robot = Articulation(robot_cfg)
        contact = ContactSensor(ContactSensorCfg(prim_path="/World/Robot/.*_foot", update_period=0.0, history_length=3))
        camera = None
        if args.video:
            camera = Camera(CameraCfg(
                prim_path="/World/Camera", height=480, width=640,
                data_types=["rgb"], update_period=0.0,
                spawn=sim_utils.PinholeCameraCfg(focal_length=24.0, clipping_range=(0.1, 100.0)),
            ))
        sim.reset()
        metadata["asset_uri"] = robot_cfg.spawn.usd_path
        metadata["joint_names"] = robot.joint_names
        metadata["foot_names"] = contact.body_names
        metadata["actuator"] = {
            "type": "DCMotor", "effort_limit_Nm": 33.5, "velocity_limit_rad_s": 21.0,
            "stiffness_Nm_rad": 25.0, "damping_Nm_s_rad": 0.5,
            "source": "Isaac Lab 2.1.1 UNITREE_A1_CFG; not hardware identification",
        }
        if robot.num_joints != 12 or len(contact.body_names) != 4:
            raise RuntimeError("Expected 12 joints and four feet")
        if camera:
            camera.set_world_poses_from_view(
                torch.tensor([[1.5, 1.5, 1.0]], device=sim.device),
                torch.tensor([[0.0, 0.0, 0.25]], device=sim.device),
            )
            for _ in range(30):
                sim.render()
            import imageio.v2 as imageio
            writer = imageio.get_writer(str(args.out / "a1.mp4"), fps=25, codec="libx264")
        root = robot.data.default_root_state.clone()
        robot.write_root_pose_to_sim(root[:, :7])
        robot.write_root_velocity_to_sim(root[:, 7:])
        robot.write_joint_state_to_sim(robot.data.default_joint_pos, robot.data.default_joint_vel)
        robot.reset()
        contact.reset()
        trace, frames = [], 0
        start = time.perf_counter()
        stride = max(1, round(1.0 / (25 * cfg["physics_dt_s"])))
        for step in range(cfg["steps"]):
            robot.set_joint_position_target(robot.data.default_joint_pos)
            robot.write_data_to_sim()
            sim.step(render=bool(camera) and step % stride == 0)
            robot.update(cfg["physics_dt_s"])
            contact.update(cfg["physics_dt_s"], force_recompute=True)
            state = robot.data.root_state_w[0].detach().cpu().numpy()
            forces = contact.data.net_forces_w[0].detach().cpu().numpy()
            if not np.isfinite(state).all() or not np.isfinite(forces).all():
                raise RuntimeError("Nonfinite state/contact")
            trace.append(np.concatenate(([(step + 1) * cfg["physics_dt_s"]], state, forces.reshape(-1))))
            if camera and step % stride == 0:
                camera.update(cfg["physics_dt_s"] * stride, force_recompute=True)
                frame = camera.data.output["rgb"][0, ..., :3].cpu().numpy()
                writer.append_data(frame)
                if frames == 0:
                    imageio.imwrite(args.out / "first-frame.png", frame)
                frames += 1
        if writer:
            writer.close()
            writer = None
        values = np.asarray(trace)
        np.savez_compressed(args.out / "trace.npz", values=values)
        metadata["trace_columns"] = "time_s, root_state_w[13] (position, quaternion wxyz, linear/angular velocity), foot_net_forces_w[4,3]"
        metadata["physics_steps"] = len(trace)
        metadata["simulation_seconds"] = len(trace) * cfg["physics_dt_s"]
        metadata["loop_wall_seconds"] = time.perf_counter() - start
        metadata["frames"] = frames
        metadata["final_base_height_m"] = float(state[2])
        metadata["max_foot_force_N"] = float(np.linalg.norm(values[:, 14:].reshape(-1, 4, 3), axis=-1).max())
        if metadata["max_foot_force_N"] <= 1.0 or state[2] < 0.15:
            raise RuntimeError("No meaningful foot contact or base collapsed")
        metadata["artifacts"] = {
            p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in args.out.iterdir() if p.suffix in (".npz", ".mp4", ".png")
        }
        metadata["status"] = "SUCCEEDED"
    except BaseException as exc:
        metadata["status"] = "FAILED"
        metadata["error"] = repr(exc)
        raise
    finally:
        if writer:
            writer.close()
        metadata["finished_unix_s"] = time.time()
        save_json(args.out / "run.json", metadata)
        print(json.dumps(metadata), flush=True)
        if app:
            # Results are durable before the bounded, process-local teardown.
            def shutdown_timeout():
                metadata["shutdown"] = "forced_after_20_seconds"
                save_json(args.out / "run.json", metadata)
                os._exit(2)

            watchdog = threading.Timer(20.0, shutdown_timeout)
            watchdog.daemon = True
            watchdog.start()
            app.close(wait_for_replicator=False)
            watchdog.cancel()
            metadata["shutdown"] = "clean"
            save_json(args.out / "run.json", metadata)


if __name__ == "__main__":
    main()
