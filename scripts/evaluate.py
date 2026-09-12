"""Fixed, complete first-episode evaluation, with optional original-frame MP4."""
from __future__ import annotations
import argparse
import copy
import json
import math
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
    p.add_argument("--video-envs", type=int, default=16)
    p.add_argument("--video-camera-side", type=int, help="Camera distance in grid-side units; 4 preserves the 16-robot framing")
    p.add_argument("--diagnostics", action="store_true")
    p.add_argument("--restore-transition", type=Path, help="Probe a saved landing state; success is for the remaining hop only")
    p.add_argument("--transition-states", action="store_true", help="Record articulated successful-landing states; replay not yet validated")
    p.add_argument("--reward-components", action="store_true", help="Audit grouped control-step rewards without changing the policy or reward")
    p.add_argument('--chain-hops', type=int, choices=[1, 2, 3, 4], help='P2-32 frozen-policy deck evaluation; separate course success contract')
    p.add_argument('--mapped-contact-progress', action='store_true', help='Separate mapped foothold course contract; retains strict trunk-flight metric')
    p.add_argument('--chain-settle-mode', choices=['default', 'hold-last'], default='default')
    p.add_argument('--action-mode', choices=['mean', 'sampled'], default='mean')
    p.add_argument('--action-seed', type=int, default=20000)
    p.add_argument("--research-tag", action="append", default=[])
    p.add_argument('--launch-radius', type=float, help='Evaluation-only tighter directed-jump launch radius in metres')
    p.add_argument('--evaluation-forward-m', nargs='+', type=float, help='Explicit evaluation-only distances on continuous/split support')
    p.add_argument('--map-goal-forward-m', type=float, help='Select a geometric stance path from the support map to a forward goal')
    p.add_argument('--support-mode', choices=['flat', 'continuous', 'split', 'deck', 'course'])
    p.add_argument('--support-matched-material', action='store_true')
    p.add_argument('--independent-support-clones', action='store_true', help='P2-38 all-deck scene construction validation only')
    p.add_argument('--support-preserve-goals', action='store_true', help='Keep configured evaluation distances during a terrain override')
    p.add_argument('--support-calibration', type=Path, help='Frozen flat evaluation run.json for support transfer')
    p.add_argument('--support-probe-offset', type=float, choices=[.075], help='Zero-action geometry probe only: start feet above the gap')
    args = p.parse_args()
    if args.chain_settle_mode != 'default' and args.chain_hops not in (2,3,4):
        p.error('Holding last action requires two-hop chain evaluation')
    if args.chain_hops is not None and ((args.chain_hops >= 2 and args.support_mode not in ('deck', 'course')) or not args.support_matched_material
            or args.support_preserve_goals or args.support_probe_offset is not None
            or args.baseline != 'policy' or args.action_mode != 'mean' or args.launch_radius is not None):
        p.error('Chain evaluation requires matched support, policy mean and original launch radius; two hops require deck or course')
    if args.action_mode == 'sampled' and args.baseline != 'policy':
        p.error('Sampled action diagnosis requires the policy baseline')
    if args.baseline != "zero" and not args.checkpoint:
        p.error("policy evaluation requires checkpoint")
    if args.video_envs < 1 or (args.video_camera_side is not None and args.video_camera_side < 1):
        p.error("Video robot count and camera side must be positive")
    config = json.loads(args.config.read_text())
    if config.get('chain_training') is not None and args.chain_hops is None:
        args.chain_hops = config['chain_training']['hops']
        args.chain_settle_mode = config['chain_training']['settle_command']
    support = None
    if args.support_mode:
        if not args.support_calibration or config['task'] != 'a1_directed_jump_v5':
            p.error('Support transfer requires directed jump and a reference calibration')
        reference = json.loads(args.support_calibration.read_text())
        if reference['status'] != 'SUCCEEDED' or reference['config']['task'] != config['task']:
            p.error('Reference must be a successful evaluation of the same task')
        from parkour.support_geometry import build_support_layout
        # Actual asset order is asserted by SequentialEnv before any policy step.
        names = ['FL_foot', 'FR_foot', 'RL_foot', 'RR_foot']
        support = {'mode': args.support_mode, 'foot_names': names,
                   'matched_material': args.support_matched_material,
                   'calibration': reference['stance_calibration'],
                   'reference_path': str(args.support_calibration.resolve()),
                   'reference_sha256': sha256(args.support_calibration),
                   'goal_forward_m': .15}
        if args.support_mode != 'flat':
            support['layout'] = build_support_layout(names, support['calibration']['foot_xy_m'], mode=args.support_mode, course_hops=args.chain_hops or 2)
        if args.support_preserve_goals:
            support.pop('goal_forward_m')
    elif args.support_calibration:
        p.error('--support-calibration requires --support-mode')
    if args.support_matched_material and not support:
        p.error('--support-matched-material requires a support mode')
    if args.support_preserve_goals and not support:
        p.error('--support-preserve-goals requires a support mode')
    if args.support_probe_offset is not None:
        if not support or args.baseline != 'zero':
            p.error('Support offset is restricted to zero-action geometry probes')
        support['probe_initial_x_offset_m'] = args.support_probe_offset
    if args.launch_radius is not None:
        if (not args.checkpoint or config['task'] != 'a1_directed_jump_v5'
                or not math.isfinite(args.launch_radius)
                or not 0 < args.launch_radius <= config['jump']['launch_radius_m']):
            p.error('Launch override requires a directed-jump checkpoint and a positive, no-larger radius')
    if args.research_tag:config["research_tags"] = args.research_tag
    manifest = development_scenarios(args.episodes, config["target_offset_m"], config.get('sequence'))
    if config.get('jump'):
        from parkour.scenarios import jump_scenarios
        manifest=jump_scenarios(args.episodes,config['jump'])
        if config['jump'].get('evaluation_forward_m') is not None:
            from parkour.scenarios import directed_jump_scenarios
            manifest=directed_jump_scenarios(args.episodes,config['jump'])
    if support and not args.support_preserve_goals:
        from parkour.scenarios import directed_jump_scenarios
        specification = copy.deepcopy(config['jump'])
        specification['evaluation_forward_m'] = [.15]
        manifest = directed_jump_scenarios(args.episodes, specification)
        manifest['evaluation_support'] = support
    if support is None and config.get('terrain_contract'):
        from parkour.terrain_contract import training_support
        support = training_support(config)
        manifest['evaluation_support'] = support
    distance_change = None
    if args.evaluation_forward_m is not None:
        if not args.checkpoint or args.support_mode not in ('continuous','split','deck') or args.support_probe_offset is not None:
            p.error('Distance override requires a checkpoint and explicit continuous/split/deck support')
        from parkour.evaluation_distance import distance_override
        manifest, distance_change = distance_override(config, support, args.evaluation_forward_m, args.episodes)
        support = copy.deepcopy(support)
        support.pop('goal_forward_m', None)
        manifest['evaluation_support'] = support
    if args.mapped_contact_progress and (args.support_mode!='course' or args.chain_hops not in (2,3,4) or args.restore_transition):
        p.error('Mapped contact progression requires an original course evaluation')
    plan = None
    if args.map_goal_forward_m is not None:
        if args.support_mode != 'course' or args.chain_hops not in (2,3,4):
            p.error('Geometric execution currently requires the two-hop course adapter')
        from parkour.geometric_planner import plan_stances
        plan = plan_stances(support['layout'], support['calibration']['foot_xy_m'], args.map_goal_forward_m, max_hops=args.chain_hops)
        selected = [c['forward_m'] for c in plan['contacts']]
        if plan['status'] != 'planned' or (len(selected)!=args.chain_hops or any(abs(x-.15*(i+1))>1e-7 for i,x in enumerate(selected))):
            p.error('No geometric plan compatible with the current 15cm two-hop Tracker contract')
        for episode in manifest['episodes']:
            episode['foot_offsets_xy_m'] = [[selected[0], 0.] for _ in range(4)]
        manifest['geometric_plan'] = plan
    manifest["task"] = config["task"]
    if config.get("sequence"):manifest["sequence_contract"] = config["sequence"]
    config["num_envs"] = args.episodes
    config["seed"] = 10000
    meta = begin_run(args.out, config, "evaluate")
    if args.chain_hops is not None:
        meta['chain_contract'] = {'schema_version': 1, 'hops': args.chain_hops,
            'settle_command': args.chain_settle_mode,
            'absolute_forward_targets_m': [.15 * (i + 1) for i in range(args.chain_hops)],
            'hop_seconds': 4., 'episode_seconds': 4. * args.chain_hops,
            'transition': 'stabilize then jump; physical state preserved; local bookkeeping only',
            'checkpoint_contract': 'original config restored strictly; runtime evaluation adapter'}
        if args.chain_hops == 1:
            distances = sorted({e['goal_forward_m'] for e in manifest['episodes']})
            meta['chain_contract']['absolute_forward_targets_m'] = distances if len(distances) == 1 else None
            meta['chain_contract']['single_hop_goal_choices_m'] = distances
            meta['chain_contract']['target_source'] = 'scenarios.episodes[*].foot_offsets_xy_m'
        if args.mapped_contact_progress:
            meta['chain_contract']['progress_criterion']='mapped_contact_v1'
        manifest['chain_contract'] = meta['chain_contract']
    if plan is not None:
        atomic_json(args.out/'geometric-plan.json', plan)
        meta['geometric_plan'] = plan
        meta['chain_contract']['target_source'] = 'geometric-plan.json contacts; Tracker-compatible translation path'
    if support:
        meta['evaluation_support'] = support
        atomic_json(args.out/'terrain.json', support)
    if distance_change is not None:meta["evaluation_distance_override"] = distance_change
    recorder = None
    try:
        launch_app(args.video)
        import numpy as np
        import torch
        from parkour.learning import make_env, make_algorithm, read_checkpoint, restore
        torch.manual_seed(10000)
        env = make_env(config, evaluation_support=support, chain_hops=args.chain_hops,
                       chain_settle_mode=args.chain_settle_mode, independent_support_clones=args.independent_support_clones, mapped_contact_progress=args.mapped_contact_progress)
        if plan is not None:
            env.planned_forward_targets = [c['forward_m'] for c in plan['contacts']]
        if args.independent_support_clones:
            from parkour.support_inspection import inspect_support_assignment
            meta['scene_construction'] = 'independent all-deck supports; replicate_physics=False; explicit collision filter'
            atomic_json(args.out/'support-assignment.json', env.cfg.support_assignment)
            atomic_json(args.out/'support-inspection.json', inspect_support_assignment(env))
        if support:
            from parkour.collision_contract import inspect_collision_contract
            contract = inspect_collision_contract(env)
            atomic_json(args.out/'collision-contract.json', contract)
        if args.transition_states:
            if args.chain_hops not in (2,3,4):
                raise ValueError('Transition states require two-hop evaluation')
            env.capture_transition_states = True
        alg, norm = make_algorithm(config, env)
        if args.checkpoint:
            data = read_checkpoint(args.checkpoint)
            restore(data, config, alg, norm, env, training=False)
            meta["checkpoint"] = {"path": str(args.checkpoint.resolve()), "sha256": sha256(args.checkpoint)}
            meta['checkpoint'].update(training_seed=data['config']['seed'], completed_iterations=data['completed_iterations'],
                                      total_environment_steps=data['total_environment_steps'])
        if args.launch_radius is not None:
            # Restore first under the original contract; training restore remains strict.
            meta['checkpoint_training_config'] = copy.deepcopy(data['config'])
            meta['evaluation_override'] = {'field': 'jump.launch_radius_m',
                'from': config['jump']['launch_radius_m'], 'to': args.launch_radius}
            config['jump']['launch_radius_m'] = args.launch_radius
            env.jump['launch_radius_m'] = args.launch_radius
            meta['config'] = config
            atomic_json(args.out / 'config.json', config)
            atomic_json(args.out / 'run.json', meta)
        alg.policy.eval()
        norm.eval()
        from parkour.evaluation_action import sample_action
        action_rng = torch.Generator(device=env.device).manual_seed(args.action_seed)
        meta['action_evaluation'] = {'mode': args.action_mode,
            'seed': args.action_seed if args.action_mode == 'sampled' else None,
            'rng_contract': 'isolated torch generator; all environment rows sampled each control step',
            'distribution': 'same diagonal Gaussian mean/std as PPO act; independent RNG stream'}
        env.reset()
        if args.support_probe_offset is not None:
            root = env.calibrated_root.expand(env.num_envs, -1).clone()
            root[:, :3] += env.scene.env_origins
            root[:, 0] += args.support_probe_offset
            env.robot.write_root_pose_to_sim(root[:, :7])
            env.robot.write_root_velocity_to_sim(root[:, 7:])
        offsets = torch.tensor([episode["foot_offsets_xy_m"] for episode in manifest["episodes"]], device=env.device)
        if hasattr(env, 'set_sequence_offsets'):
            orders=None
            if 'episode_order_indices' in manifest['episodes'][0]:
                orders=torch.tensor([e['episode_order_indices'] for e in manifest['episodes']],device=env.device)
            env.set_sequence_offsets(offsets,episode_orders=orders)
            if config.get('jump'):
                env.required_apex[:]=torch.tensor([e['required_apex_m'] for e in manifest['episodes']],device=env.device)
            meta['stance_calibration'] = env.calibration
        else:
            env.targets[:, :, :2] = env.scene.env_origins[:, None, :2] + env.nominal_xy + offsets
        atomic_json(args.out / "scenarios.json", manifest)
        meta["scenario_sha256"] = sha256(args.out / "scenarios.json")
        meta["baseline"] = args.baseline
        meta["nominal_foot_xy_m"] = env.nominal_xy.tolist()
        if args.restore_transition:
            if args.chain_hops not in (2,3,4) or args.transition_states or args.action_mode != 'mean':
                raise ValueError('Restore probe requires two-hop mean policy without nested capture')
            from parkour.transition_states import restore_transition_states
            restored = restore_transition_states(env, args.restore_transition, args.checkpoint, support)
            meta['transition_restore'] = restored
            manifest['transition_restore'] = restored
            atomic_json(args.out/'transition-restore.json', restored)
            atomic_json(args.out/'scenarios.json', manifest)
            meta['scenario_sha256'] = sha256(args.out/'scenarios.json')
        raw = env._get_observations()["policy"]
        done = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        if args.chain_hops is not None:
            env.evaluation_done = done
        reward_audit = None
        if args.reward_components:
            if config['task'] != 'a1_directed_jump_v5':
                raise ValueError('Reward accounting currently supports directed jump v5 only')
            from parkour.reward_audit import RewardAudit
            reward_audit = RewardAudit()
            env.record_reward_components = True
            meta['reward_accounting'] = 'grouped_control_step_v1'
        records = [None] * env.num_envs
        diagnostics = None
        if args.diagnostics:
            from parkour.diagnostics import MotionDiagnostics
            diagnostics = MotionDiagnostics(env, done)
        if args.video:
            from parkour.media import ParallelRecorder
            recorder = ParallelRecorder(env,args.out,count=args.video_envs,camera_side=args.video_camera_side)
        with torch.inference_mode():
            for step in range(env.max_episode_length + 1):
                if args.baseline == "zero":
                    action = torch.zeros(env.num_envs, 12, device=env.device)
                else:
                    policy_obs = raw.clone()
                    if args.baseline == "shuffled-target":
                        # Replace only target channels; the true task/reward remains unchanged.
                        policy_obs[:, 45:57] = torch.roll(policy_obs[:, 45:57], 1, dims=0)
                    normalized = norm(policy_obs)
                    action = (sample_action(alg.policy, normalized, action_rng) if args.action_mode == 'sampled'
                              else alg.policy.act_inference(normalized))
                if recorder and not bool(done[recorder.ids].all()):
                    recorder.capture(step,finished=done)
                raw_dict, reward, term, trunc, extras = env.step(action)
                if reward_audit:
                    reward_audit.collect(reward, extras['reward_components'], done)
                raw = raw_dict["policy"]
                newly_done = (term | trunc) & ~done
                for index in newly_done.nonzero().flatten().tolist():
                    metrics = extras["terminal_metrics"]
                    records[index] = {"scenario_id": manifest["episodes"][index]["id"],
                        **{key: val[index].item() for key, val in metrics.items()}}
                    if 'active_foot' in manifest['episodes'][index]:
                        records[index]['active_foot']=manifest['episodes'][index]['active_foot']
                done |= newly_done
                if bool(done.all()):
                    break
        if not bool(done.all()) or any(record is None for record in records):
            raise RuntimeError("Evaluation incomplete; missing scenario results")
        if recorder:
            recorder.close(episode=records[0], episodes=[records[i] for i in recorder.ids],
                           recording_kind='parallel_evaluation',
                           video_stop_rule='last visible first episode; subsequent auto-resets shown but excluded from metrics')
            recorder = None
        if diagnostics:
            diagnostics.close(args.out, [s["id"] for s in manifest["episodes"]])
        if reward_audit:
            reward_audit.close(args.out, manifest['episodes'], env.step_dt)
        if args.transition_states:
            from parkour.transition_states import save_transition_states
            save_transition_states(env, args.out, [s['id'] for s in manifest['episodes']])
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
        if 'completed_contacts' in records[0]:
            report['required_contacts'] = 4 if config.get('jump') else config.get('sequence',{}).get('sequence_length',4)
            report['mean_completed_contacts'] = sum(row['completed_contacts'] for row in records)/count
        if 'valid_flight' in records[0]:
            report['valid_flights']=sum(r['valid_flight'] for r in records)
            report['landed_episodes']=sum(r['landed'] for r in records)
            report['mean_flight_apex_rise_m']=sum(r['flight_apex_rise_m'] for r in records)/count
            report['nonfoot_collisions']=sum(r['nonfoot_collision'] for r in records)
        if 'first_touch_count' in records[0]:
            report['first_touch_precise_episodes']=sum(r['first_touch_all_within'] for r in records)
            report['stabilized_episodes']=sum(r['stabilized_once'] for r in records)
            report['success_contract']='verified flight + precise first touch + final stabilization'
        if 'goal_forward_m' in records[0]:
            report['success_wilson95']=None
            report['success_interval_note']='같은 높이 명령을 거리별로 재사용하므로 전체 episode를 독립 표본으로 간주한 Wilson 구간은 제공하지 않습니다. 거리별 결과와 학습 seed별 변동을 확인하세요.'
            report['success_contract']='verified flight from launch region + minimum airborne travel + precise first touch + stabilization'
            from parkour.evaluation_summary import by_distance
            report['by_distance'] = by_distance(records, manifest['episodes'])
        if 'active_foot' in records[0]:
            report['by_foot']={}
            for foot in env.foot_names:
                subset=[r for r in records if r['active_foot']==foot]
                if subset:
                    report['by_foot'][foot]={'episodes':len(subset),'successes':sum(r['success'] for r in subset),
                        'placed':sum(r['completed_contacts']==report['required_contacts'] for r in subset),
                        'failures':sum(r['failure'] for r in subset),'timeouts':sum(r['timeout'] for r in subset)}
        if args.chain_hops is not None:
            report['chain_contract'] = meta['chain_contract']
            report['success_contract'] = 'all commanded hops independently pass flight/travel/first-touch/stabilization, without intermediate physical reset'
            report['completed_hops_histogram'] = {str(i): sum(r['completed_hops'] == i for r in records) for i in range(args.chain_hops + 1)}
            report['hop_diagnostic_scope'] = 'legacy flight/contact fields describe the final attempted hop; return and mean error span the course'
            atomic_json(args.out / 'chain-events.json', {'contract': meta['chain_contract'],
                'hops': env.hop_events, 'transitions': env.transition_events,
                'scope': 'first episode per environment only; later auto-reset episodes excluded'})
        if args.mapped_contact_progress:
            report['success_contract']='valid flight + launch region + first contact on assigned surface + precise stable support; trunk airborne distance is a separate legacy metric'
            report['evaluation_scope']='mapped_contact_v1; not comparable to legacy strict-travel success'
        if args.restore_transition:
            report['evaluation_scope'] = 'restored_remaining_hop_only'
            report['success_contract'] = 'Remaining hop from restored landing passes original gates; prior hop not executed in this run'
            report['course_successes'] = None
            report['restored_prior_hops'] = 1
            report['hop_diagnostic_scope'] = 'return/errors describe restored segment; length retains source episode clock'
        atomic_json(args.out / "evaluation.json", report)
        meta["evaluation"] = {key: value for key, value in report.items() if key != "results"}
        meta["artifacts"] = {file.name: sha256(file) for file in args.out.iterdir()
                             if file.suffix in (".mp4", ".png") or file.name in ("transition-restore.json", "transition-states.json", "transition-states.npz", "geometric-plan.json", "collision-contract.json", "terrain.json", "evaluation.json", "scenarios.json", "replay.json", "diagnostics.json", "motion-trace.npz", "reward-components.json", "reward-components.npz")}
        if args.chain_hops is not None:
            meta['artifacts']['chain-events.json'] = sha256(args.out / 'chain-events.json')
        if args.independent_support_clones:
            for name in ('support-assignment.json', 'support-inspection.json'):
                meta['artifacts'][name] = sha256(args.out / name)
        finish_run(args.out, meta)
    except BaseException as exc:
        if recorder and recorder.writer:
            recorder.writer.close()
        traceback.print_exc()
        finish_run(args.out, meta, exc)


if __name__ == "__main__":
    main()
