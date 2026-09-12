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
    from parkour.contact_curriculum import radius_for_update as contact_radius_for_update
    contact_radius_for_update(config,0)
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
        if env.cfg.support_assignment:
            from parkour.support_inspection import inspect_support_assignment
            atomic_json(args.out/'support-assignment.json', env.cfg.support_assignment)
            atomic_json(args.out/'support-inspection.json', inspect_support_assignment(env))
        env.reset()
        alg, norm = make_algorithm(config, env)
        from parkour.learning import model_profile
        meta['model_profile']=model_profile(config,alg,norm,env)
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
        goal_values=getattr(env, 'goal_sample_values', [])
        retention = getattr(env, 'retention_enabled', False)
        if retention:
            meta['retention_accounting_contract'] = 'task rows chain,single; hop columns first,second; pre-action steps; current-policy shared PPO rollout'
            meta['single_goal_initial_draws'] = env.single_goal_draw_counts.tolist()
        if goal_values:
            meta['goal_accounting_initial_draws'] = dict(zip(map(str,goal_values),env.goal_draw_counts.tolist()))
            meta['goal_accounting_contract'] = 'Per-attempt reset draws; pre-action environment transitions; initialization draws separate; counters are diagnostics, not curriculum state'
        rollout_step=0
        for iteration in range(completed, completed + config["iterations"]):
            started = time.perf_counter()
            exploration_cap = cap_for_update(config, iteration)
            if exploration_cap is not None:
                alg.policy.std_cap.fill_(exploration_cap)
            transition = False
            contact_radius=contact_radius_for_update(config,iteration)
            if contact_radius is not None and env.cfg.success_radius_m!=contact_radius:
                env.cfg.success_radius_m=contact_radius
                with torch.inference_mode():
                    raw,_=env.reset();obs=norm(raw['policy'])
                transition=True
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
            terminal_transfers,terminal_jumps,terminal_seconds=[],[],[]
            jump_flights,jump_landings,jump_apex_met=0,0,0
            jump_apices=[]
            if hasattr(env, 'chain'):
                hop_steps = torch.zeros(env.chain.hops, dtype=torch.long, device=env.device)
                hop_successes = torch.zeros_like(hop_steps)
                hop_returns = torch.zeros(env.chain.hops, device=env.device)
            if goal_values:
                draws_before=env.goal_draw_counts.clone()
                goal_steps=torch.zeros(len(goal_values),dtype=torch.long,device=env.device)
            if retention:
                task_hop_steps = torch.zeros((2, 2), dtype=torch.long, device=env.device)
                task_episodes = torch.zeros(2, dtype=torch.long, device=env.device)
                task_successes = torch.zeros_like(task_episodes)
                task_rewards = torch.zeros(2, device=env.device)
                single_goal_steps = torch.zeros(len(env.goal_sample_values), dtype=torch.long, device=env.device)
                single_draws_before = env.single_goal_draw_counts.clone()
            with torch.inference_mode():
                for _ in range(steps_per_iteration):
                    if hasattr(env, 'chain'):
                        segments = env.chain.completed.clone()
                        hop_steps += torch.bincount(segments, minlength=env.chain.hops)
                    if retention:
                        task_hop_steps += torch.bincount(env.retention_task * 2 + segments, minlength=4).reshape(2, 2)
                        for i, distance in enumerate(env.goal_sample_values):
                            single_goal_steps[i] += ((env.retention_task == 1) & ((env.goal_distance - distance).abs() < 1e-7)).sum()
                    if goal_values:
                        for goal_index,goal_value in enumerate(goal_values):
                            goal_steps[goal_index]+=(torch.abs(env.goal_distance-goal_value)<1e-7).sum()
                    actions = alg.act(obs, obs)
                    if recorder:
                        recorder.capture(rollout_step,iteration=iteration+1)
                    rollout_step+=1
                    raw, rewards, term, trunc, extras = env.step(actions)
                    obs = norm(raw["policy"])
                    if not torch.isfinite(obs).all() or not torch.isfinite(rewards).all():
                        raise RuntimeError("Nonfinite observation/reward")
                    dones = term | trunc
                    if hasattr(env, 'chain'):
                        hop_metrics = extras['terminal_metrics']
                        passed = hop_metrics['hop_success']
                        intermediate = passed & (segments < env.chain.target_hops - 1)
                        if bool((intermediate & dones).any()):
                            raise RuntimeError('Successful intermediate hop unexpectedly ended training episode')
                        hop_successes += torch.bincount(segments[passed], minlength=env.chain.hops)
                        hop_returns.scatter_add_(0, segments, rewards)
                    if retention:
                        task_rewards.scatter_add_(0, env.retention_task, rewards)
                        task_episodes += torch.bincount(env.retention_task[dones], minlength=2)
                        succeeded = dones & extras['terminal_metrics']['success']
                        task_successes += torch.bincount(env.retention_task[succeeded], minlength=2)
                    alg.process_env_step(rewards, dones, {"time_outs": trunc})
                    if dones.any():
                        metrics = extras["terminal_metrics"]
                        successes += int(metrics["success"][dones].sum())
                        failures += int(metrics["failure"][dones].sum())
                        episodes += int(dones.sum())
                        errors.extend(metrics["final_error_m"][dones].tolist())
                        if 'completed_surface_transfers' in metrics:
                            terminal_transfers.extend(metrics['completed_surface_transfers'][dones].tolist())
                            terminal_jumps.extend(metrics['measured_jump_count'][dones].tolist())
                            terminal_seconds.extend((metrics['length'][dones]*env.step_dt).tolist())
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
            if goal_values:
                if int(goal_steps.sum()) != env.num_envs*steps_per_iteration:
                    raise RuntimeError('Goal accounting did not cover every transition')
                row['goal_environment_steps'] = dict(zip(map(str,goal_values),goal_steps.tolist()))
                row['goal_reset_draws'] = dict(zip(map(str,goal_values),(env.goal_draw_counts-draws_before).tolist()))
                row['train_forward_choices_m'] = config['jump'].get('train_forward_choices_m')
            if hasattr(env, 'chain'):
                if int(hop_steps.sum()) != env.num_envs * steps_per_iteration:
                    raise RuntimeError('Hop accounting did not cover every PPO transition')
                row['hop_environment_steps'] = hop_steps.tolist()
                row['hop_successes'] = hop_successes.tolist()
                row['hop_reward_sums'] = hop_returns.tolist()
                row['jump_metric_scope'] = 'terminal hop diagnostics; success means complete course'
            if retention:
                expected = env.num_envs * steps_per_iteration // 2
                if (task_hop_steps.sum(1).tolist() != [expected, expected]
                        or int(task_hop_steps[1, 1]) != 0 or int(single_goal_steps.sum()) != expected
                        or int(task_episodes.sum()) != episodes or int(task_successes.sum()) != successes):
                    raise RuntimeError('Retention task accounting inconsistent with PPO transitions or terminations')
                row.update(task_hop_environment_steps=task_hop_steps.tolist(),
                           task_episodes=task_episodes.tolist(), task_successes=task_successes.tolist(),
                           task_reward_sums=task_rewards.tolist(), single_goal_environment_steps=single_goal_steps.tolist(),
                           single_goal_reset_draws=(env.single_goal_draw_counts - single_draws_before).tolist())
            if contact_radius is not None:
                row.update(training_contact_radius_m=contact_radius,strict_evaluation_contact_radius_m=config['success_radius_m'],
                           contact_curriculum_reset_all=transition)
            if exploration_cap is not None:
                effective=alg.policy.std.detach().clamp(min=alg.policy.std_floor,max=alg.policy.std_cap)
                row.update(exploration_std_cap=exploration_cap, exploration_std_min=float(effective.min()),
                           exploration_std_max=float(effective.max()),exploration_std_mean=float(effective.mean()))
            if hasattr(env,'progress'):
                from collections import Counter
                row['terminal_surface_transfer_histogram']=dict(Counter(map(str,terminal_transfers)))
                row['terminal_mean_surface_transfers']=sum(terminal_transfers)/len(terminal_transfers) if terminal_transfers else None
                row['terminal_mean_measured_jumps']=sum(terminal_jumps)/len(terminal_jumps) if terminal_jumps else None
                row['terminal_mean_episode_seconds']=sum(terminal_seconds)/len(terminal_seconds) if terminal_seconds else None
                row['contact_target_mode']=env.cfg.contact_target_mode
                row['live_mean_front_accepted_index']=float(env.progress.accepted[:,0].float().mean())
                row['live_mean_rear_accepted_index']=float(env.progress.accepted[:,1].float().mean())
                row['required_final_index']=env.progress.target_count-1
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
            if env.cfg.support_assignment:
                for name in ('support-assignment.json', 'support-inspection.json'):
                    meta['artifacts'][name] = sha256(args.out/name)
        finish_run(args.out, meta)
    except BaseException as exc:
        if recorder and recorder.writer:
            recorder.writer.close()
        traceback.print_exc()
        finish_run(args.out, meta, exc)


if __name__ == "__main__":
    main()
