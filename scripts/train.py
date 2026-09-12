"""A bounded, local PPO training attempt for the T0 foothold task."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import time
import traceback
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parkour.runtime import begin_run, finish_run, launch_app, atomic_json, sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/t0-ppo.json"))
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int)
    p.add_argument("--iterations", type=int)
    p.add_argument("--num-envs", type=int)
    initialization = p.add_mutually_exclusive_group()
    initialization.add_argument("--resume", type=Path)
    initialization.add_argument("--fork-from", type=Path)
    p.add_argument("--video", action="store_true", help="Record real parallel PPO updates for this bounded attempt")
    args = p.parse_args()
    config = json.loads(args.config.read_text())
    for key in ("seed", "iterations", "num_envs"):
        if getattr(args, key) is not None:
            config[key] = getattr(args, key)
    if config["iterations"] < 1 or config["num_envs"] < 1:
        raise ValueError("Positive iterations and num-envs required")
    from parkour.launch_curriculum import radius_for_update, distance_for_update
    radius_for_update(config, 0)  # Validate the complete schedule before simulator startup.
    distance_for_update(config, 0)
    from parkour.terrain_contract import training_support
    support = training_support(config)
    meta = begin_run(args.out, config, "train")
    recorder = None
    try:
        launch_app(args.video)
        import random
        import numpy as np
        import torch
        from parkour.learning import make_env, make_algorithm, read_checkpoint, restore, save_checkpoint
        from parkour.exploration import cap_for_update
        cap_for_update(config,0)
        random.seed(config["seed"])
        np.random.seed(config["seed"])
        torch.manual_seed(config["seed"])
        torch.set_num_threads(4)
        env = make_env(config)
        if support:
            from parkour.collision_contract import inspect_collision_contract
            atomic_json(args.out/'terrain.json', support)
            atomic_json(args.out/'collision-contract.json', inspect_collision_contract(env))
            meta['terrain_contract'] = support
        env.reset()
        alg, norm = make_algorithm(config, env)
        completed, total_steps = 0, 0
        if args.resume:
            data = read_checkpoint(args.resume)
            restore(data, config, alg, norm, env, training=True)
            completed, total_steps = data["completed_iterations"], data["total_environment_steps"]
            meta["parent_checkpoint"] = {"path": str(args.resume.resolve()), "sha256": sha256(args.resume)}
            meta["resume_contract"] = data["resume_contract"]
            if data.get("lineage") is not None:meta["lineage"] = data["lineage"]
        elif args.fork_from:
            from parkour.policy_fork import initialize_fork
            data = read_checkpoint(args.fork_from)
            meta["lineage"] = initialize_fork(data, config, alg, norm)
            meta["lineage"]["parent_checkpoint"] = {"path": str(args.fork_from.resolve()), "sha256": sha256(args.fork_from)}
            atomic_json(args.out / "run.json", meta)
            save_checkpoint(args.out / "checkpoint-000000.pt", config, alg, norm, env, 0, 0, lineage=meta["lineage"])
        active_radius = radius_for_update(config, completed)
        active_distance = distance_for_update(config, completed)
        if config.get('jump', {}).get('distance_curriculum') is not None:
            env.jump['train_forward_range_m'] = active_distance
        if config.get("jump", {}).get("launch_curriculum") is not None:
            env.jump["launch_radius_m"] = active_radius
        raw, _ = env.reset()
        alg.policy.train()
        norm.train()
        with torch.inference_mode():
            obs = norm(raw["policy"])
        steps_per_iteration = config["runner"]["num_steps_per_env"]
        meta["nominal_foot_xy_m"] = env.nominal_xy.tolist()
        if hasattr(env, 'calibration'):
            meta['stance_calibration'] = env.calibration
        metrics_file = (args.out / "metrics.jsonl").open("w", buffering=1)
        if args.video:
            from parkour.media import ParallelRecorder
            recorder=ParallelRecorder(env,args.out,name='parallel-training')
        rollout_step=0
        for iteration in range(completed, completed + config["iterations"]):
            started = time.perf_counter()
            exploration_cap = cap_for_update(config, iteration)
            if exploration_cap is not None:
                alg.policy.std_cap.fill_(exploration_cap)
            transition = False
            next_radius = radius_for_update(config, iteration)
            next_distance = distance_for_update(config, iteration)
            if next_radius != active_radius or next_distance != active_distance:
                env.jump["launch_radius_m"] = next_radius
                active_radius = next_radius
                if next_distance is not None:
                    env.jump['train_forward_range_m'] = next_distance
                active_distance = next_distance
                with torch.inference_mode():
                    raw, _ = env.reset()
                    obs = norm(raw["policy"])
                transition = True
            successes, failures, episodes, errors = 0, 0, 0, []
            completed_contacts = []
            jump_flights,jump_landings,jump_apex_met=0,0,0
            jump_apices=[]
            with torch.inference_mode():
                for _ in range(steps_per_iteration):
                    actions = alg.act(obs, obs)
                    if recorder:
                        recorder.capture(rollout_step,iteration=iteration+1)
                    rollout_step+=1
                    raw, rewards, term, trunc, extras = env.step(actions)
                    obs = norm(raw["policy"])
                    if not torch.isfinite(obs).all() or not torch.isfinite(rewards).all():
                        raise RuntimeError("Nonfinite observation/reward")
                    dones = term | trunc
                    alg.process_env_step(rewards, dones, {"time_outs": trunc})
                    if dones.any():
                        metrics = extras["terminal_metrics"]
                        successes += int(metrics["success"][dones].sum())
                        failures += int(metrics["failure"][dones].sum())
                        episodes += int(dones.sum())
                        errors.extend(metrics["final_error_m"][dones].tolist())
                        if 'valid_flight' in metrics:
                            jump_flights+=int(metrics['valid_flight'][dones].sum())
                            jump_landings+=int(metrics['landed'][dones].sum())
                            jump_apices.extend(metrics['flight_apex_rise_m'][dones].tolist())
                            jump_apex_met+=int((metrics['valid_flight'][dones] & (metrics['flight_apex_rise_m'][dones]>=metrics['required_apex_m'][dones])).sum())
                        if 'completed_contacts' in metrics:
                            completed_contacts.extend(metrics['completed_contacts'][dones].tolist())
                alg.compute_returns(obs)
            losses = alg.update()
            if not all(torch.isfinite(param).all() for param in alg.policy.parameters()):
                raise RuntimeError("Nonfinite policy parameters")
            total_steps += env.num_envs * steps_per_iteration
            row = {"iteration": iteration + 1, "total_environment_steps": total_steps,
                   "wall_seconds": time.perf_counter() - started, "episodes": episodes,
                   "successes": successes, "failures": failures,
                   "mean_final_error_m": sum(errors) / len(errors) if errors else None,
                   "losses": {k: float(v) for k, v in losses.items()}}
            if exploration_cap is not None:
                effective=alg.policy.std.detach().clamp(min=alg.policy.std_floor,max=alg.policy.std_cap)
                row.update(exploration_std_cap=exploration_cap, exploration_std_min=float(effective.min()),
                           exploration_std_max=float(effective.max()),exploration_std_mean=float(effective.mean()))
            if config.get('jump'):
                row['launch_radius_m'] = active_radius
                row['curriculum_reset_all'] = transition
                row['train_forward_range_m'] = active_distance
                row['valid_flights']=jump_flights;row['landed_episodes']=jump_landings
                row['apex_command_met']=jump_apex_met
                row['mean_flight_apex_rise_m']=sum(jump_apices)/len(jump_apices) if jump_apices else None
            if completed_contacts:
                row['mean_completed_contacts'] = sum(completed_contacts)/len(completed_contacts)
            metrics_file.write(json.dumps(row, allow_nan=False) + "\n")
            print(json.dumps(row), flush=True)
            meta["last_iteration"] = iteration + 1
            meta["heartbeat_unix_s"] = time.time()
            atomic_json(args.out / "run.json", meta)
            if (iteration + 1) % config["runner"]["save_interval"] == 0:
                save_checkpoint(args.out / f"checkpoint-{iteration + 1:06d}.pt", config, alg, norm, env, iteration + 1, total_steps, lineage=meta.get("lineage"))
        final = args.out / f"checkpoint-{iteration + 1:06d}.pt"
        if not final.exists():
            save_checkpoint(final, config, alg, norm, env, iteration + 1, total_steps, lineage=meta.get("lineage"))
        metrics_file.close()
        if recorder:
            payload=recorder.close(recording_kind='actual_parallel_ppo_training',
                                   learning_iterations=[completed+1,iteration+1],
                                   note='All environments simulate; only a 4x4 grid is visible. Optimizer updates occur between rollout batches.')
            recorder=None
            meta['training_video']={'file':'parallel-training.mp4','sha256':sha256(args.out/'parallel-training.mp4'),
                                    'visible_env_ids':payload['visible_env_ids'],'total_simulated_envs':env.num_envs,
                                    'learning_iterations':[completed+1,iteration+1]}
        meta["checkpoint"] = {"path": final.name, "sha256": sha256(final)}
        meta["total_environment_steps"] = total_steps
        if support:
            meta['artifacts'] = {name: sha256(args.out/name) for name in ('terrain.json', 'collision-contract.json')}
        finish_run(args.out, meta)
    except BaseException as exc:
        if recorder and recorder.writer:
            recorder.writer.close()
        traceback.print_exc()
        finish_run(args.out, meta, exc)


if __name__ == "__main__":
    main()
