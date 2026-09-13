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
    p.add_argument('--terminal-policy',type=Path,help='Explicit final-stance RL checkpoint; composite evaluation only')
    p.add_argument('--terminal-pose-hold',action='store_true',help='Explicit settled joint-pose hold; hybrid evaluation only')
    p.add_argument('--terminal-pose-mode',choices=['settled','contact-capture'],default='settled')
    p.add_argument('--thesis-policy',type=Path)
    p.add_argument('--thesis-source',type=Path,default=Path('../master-thesis'))
    p.add_argument('--thesis-speed',type=float,default=.5)
    p.add_argument('--thesis-action-limit',type=float,default=1.)
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
    p.add_argument('--chain-hops', type=int, choices=range(1,9), help='Frozen-policy one-to-eight-hop evaluation; explicit course success contract')
    p.add_argument('--vectorized-map-contact', action='store_true', help='Opt-in equivalent map gate performance probe')
    p.add_argument('--curriculum-map', help='RLflow curriculum: JSON {"seed":1,"fractions":0.4 | {"base":.25,"gap":.5,...}} → parkour.curriculum_maps.build_mixed_discrete_axes')
    p.add_argument('--course-station-heights', type=float, nargs='+', help='Initial and landing support heights, one per station')
    p.add_argument('--course-friction', type=float, help='Authored static/dynamic friction for later course pads')
    p.add_argument('--friction-start-station', type=int, default=4)
    p.add_argument('--course-step-lengths', type=float, nargs='+', help='Explicit bounded variable step lengths in metres')
    p.add_argument('--map-course-boundary', action='store_true', help='Use map surface envelope plus 20cm root margin instead of legacy 60cm radius')
    p.add_argument('--mapped-contact-progress', action='store_true', help='Separate mapped foothold course contract; retains strict trunk-flight metric')
    p.add_argument('--chain-settle-mode', choices=['default', 'hold-last'], default='default')
    p.add_argument('--action-mode', choices=['mean', 'sampled'], default='mean')
    p.add_argument('--action-seed', type=int, default=20000)
    p.add_argument("--research-tag", action="append", default=[])
    p.add_argument('--launch-radius', type=float, help='Evaluation-only tighter directed-jump launch radius in metres')
    p.add_argument('--evaluation-forward-m', nargs='+', type=float, help='Explicit evaluation-only distances on continuous/split support')
    p.add_argument('--map-goal-forward-m', type=float, help='Select a geometric stance path from the support map to a forward goal')
    p.add_argument('--gap-travel-m', type=float, default=.5, help='Foot translation for disjoint whole-platform gap evaluation')
    p.add_argument('--video-camera-mode',choices=['parallel','follow'])
    p.add_argument('--video-follow-env-index',type=int,default=0)
    p.add_argument('--video-selection-reason',default='')
    p.add_argument('--shared-course-level',choices=['easy','medium','hard'])
    p.add_argument('--mixed-course-fraction',type=float,choices=[.25,.5,.75,1.])
    p.add_argument('--shared-course-seed',type=int,default=101)
    p.add_argument('--shared-course-transfers',type=int,choices=[*range(10,41),60])
    p.add_argument('--support-mode', choices=['flat', 'continuous', 'split', 'deck', 'course', 'full-gap'])
    p.add_argument('--support-matched-material', action='store_true')
    p.add_argument('--independent-support-clones', action='store_true', help='P2-38 all-deck scene construction validation only')
    p.add_argument('--support-preserve-goals', action='store_true', help='Keep configured evaluation distances during a terrain override')
    p.add_argument('--support-calibration', type=Path, help='Frozen flat evaluation run.json for support transfer')
    p.add_argument('--support-probe-offset', type=float, choices=[.075], help='Zero-action geometry probe only: start feet above the gap')
    p.add_argument('--four-step-candidate-probe',action='store_true',help='Matched policy physical rollout of nine four-step foothold candidates; requires episodes divisible by nine')
    p.add_argument('--candidate-prefix-run',type=Path,help='Replay an audited action prefix before physical candidate branching')
    p.add_argument('--candidate-prefix-steps',type=int,default=50)
    args = p.parse_args()
    if args.candidate_prefix_run and not args.four_step_candidate_probe:p.error('Prefix requires candidate probe')
    if args.chain_settle_mode != 'default' and args.chain_hops not in range(2,9):
        p.error('Holding last action requires two-hop chain evaluation')
    if args.chain_hops is not None and ((args.chain_hops >= 2 and args.support_mode not in ('deck', 'course')) or not args.support_matched_material
            or args.support_preserve_goals or args.support_probe_offset is not None
            or args.baseline != 'policy' or args.action_mode != 'mean' or args.launch_radius is not None):
        p.error('Chain evaluation requires matched support, policy mean and original launch radius; two hops require deck or course')
    if args.action_mode == 'sampled' and args.baseline != 'policy':
        p.error('Sampled action diagnosis requires the policy baseline')
    if args.thesis_policy and (args.checkpoint or args.baseline!='policy' or args.action_mode!='mean'):
        p.error('Thesis teacher is a separate frozen mean-policy probe')
    if args.baseline != "zero" and not args.checkpoint and not args.thesis_policy:
        p.error("policy evaluation requires checkpoint")
    if not 0<=args.video_follow_env_index<args.episodes:p.error('Follow index must belong to the evaluated environments')
    if args.video_follow_env_index and not args.video_selection_reason:p.error('Nondefault follow index requires an explicit selection reason')
    if args.video_envs < 1 or (args.video_camera_side is not None and args.video_camera_side < 1):
        p.error("Video robot count and camera side must be positive")
    config = json.loads(args.config.read_text())
    if args.terminal_policy and (not args.checkpoint or config['task']!='a1_continuous_tracker_v1' or args.baseline!='policy' or args.action_mode!='mean' or args.thesis_policy):
        p.error('Terminal policy requires mean continuous policy evaluation')
    if args.thesis_policy and config['task']!='a1_continuous_tracker_v1':
        p.error('Thesis teacher probe requires the new continuous course contract')
    if config.get('chain_training') is not None and args.chain_hops is None:
        args.chain_hops = config['chain_training']['hops']
        args.chain_settle_mode = config['chain_training']['settle_command']
        args.mapped_contact_progress = config['chain_training'].get('progress_criterion')=='mapped_contact_v1'
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
        if args.support_mode=='full-gap':
            if args.chain_hops!=1 or args.restore_transition or args.support_preserve_goals:
                p.error('Whole-platform gap requires explicit original one-hop evaluation')
            from parkour.support_geometry import build_full_platform_gap
            support['layout']=build_full_platform_gap(names,support['calibration']['foot_xy_m'],args.gap_travel_m)
            support['goal_forward_m']=args.gap_travel_m
        elif args.support_mode != 'flat':
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
        specification['evaluation_forward_m'] = [support.get('goal_forward_m',.15)]
        manifest = directed_jump_scenarios(args.episodes, specification)
        manifest['evaluation_support'] = support
    if support is None and config.get('terrain_contract'):
        from parkour.terrain_contract import training_support
        support = training_support(config)
        manifest['evaluation_support'] = support
    if args.shared_course_level is not None:
        if config['task']!='a1_continuous_tracker_v1' or args.support_mode:
            p.error('Shared-course evaluation override requires continuous Tracker')
        from parkour.shared_evaluation import override_course
        support=override_course(support,args.shared_course_level,args.shared_course_seed,args.shared_course_transfers)
    elif args.shared_course_transfers is not None:
        p.error('Explicit --shared-course-level required for a length override')
    if args.mixed_course_fraction is not None:
        if config['task']!='a1_continuous_tracker_v1' or args.shared_course_level is not None or args.support_mode:p.error('Mixed override requires continuous Tracker and no other terrain override')
        from parkour.shared_terrain import build_mixed_discrete
        support=copy.deepcopy(support);support['layout']=build_mixed_discrete(args.shared_course_seed,args.mixed_course_fraction);support['geometry_seed']=args.shared_course_seed
    if args.curriculum_map is not None:
        if config['task']!='a1_continuous_tracker_v1' or args.shared_course_level is not None or args.support_mode or args.mixed_course_fraction is not None:p.error('Curriculum map override requires continuous Tracker and no other terrain override')
        from parkour.curriculum_maps import build_mixed_discrete_axes
        spec=json.loads(args.curriculum_map)
        support=copy.deepcopy(support);support['layout']=build_mixed_discrete_axes(int(spec.get('seed',1)),spec.get('fractions',.25));support['geometry_seed']=int(spec.get('seed',1))
    if args.shared_course_level is not None:
        config['research_tags']=[t for t in config.get('research_tags',[]) if not t.startswith('difficulty:')]+['difficulty:'+args.shared_course_level]
    if config['task']=='a1_continuous_tracker_v1':
        if args.support_mode or args.chain_hops is not None or args.map_goal_forward_m is not None:
            p.error('Continuous Tracker uses its explicit shared-course contract, not legacy runtime adapters')
        manifest={'schema_version':2,'split':'development','contract':'shared_course_fixed_initial_state_v1',
            'episodes':[{'id':f'shared-course-dev-{i:05d}','geometry_seed':support['geometry_seed']} for i in range(args.episodes)],
            'evaluation_support':support,
            'scope':'Repeated fixed course/initial stance; environment rows are not independent terrain samples'}
    distance_change = None
    if args.evaluation_forward_m is not None:
        if not args.checkpoint or args.support_mode not in ('continuous','split','deck') or args.support_probe_offset is not None:
            p.error('Distance override requires a checkpoint and explicit continuous/split/deck support')
        from parkour.evaluation_distance import distance_override
        manifest, distance_change = distance_override(config, support, args.evaluation_forward_m, args.episodes)
        support = copy.deepcopy(support)
        support.pop('goal_forward_m', None)
        manifest['evaluation_support'] = support
    if args.course_step_lengths is not None:
        if not args.map_course_boundary or args.map_goal_forward_m is None or args.support_mode != 'course' or len(args.course_step_lengths) != args.chain_hops:
            p.error('Variable spacing requires matching course horizon, geometric goal and map boundary')
        from parkour.support_geometry import vary_course_steps
        support['layout'] = vary_course_steps(support['layout'], args.course_step_lengths)
        support.pop('goal_forward_m', None)
    if args.course_station_heights is not None:
        if (not args.map_course_boundary or args.map_goal_forward_m is None or not args.mapped_contact_progress or args.support_mode!='course' or len(args.course_station_heights)!=(args.chain_hops or 0)+1):
            p.error('Elevated course requires mapped geometric plan and one height per station')
        from parkour.support_geometry import vary_course_heights
        support['layout']=vary_course_heights(support['layout'],args.course_station_heights)
    if args.course_friction is not None:
        if (not args.map_course_boundary or args.support_mode != 'course' or not math.isfinite(args.course_friction) or not 0 <= args.course_friction <= .5 or not 1 <= args.friction_start_station <= (args.chain_hops or 0)):
            p.error('Friction override requires mapped course, valid station and finite friction in [0,.5]')
        support['surface_material_overrides'] = {surface['id']: {'static_friction': args.course_friction, 'dynamic_friction': args.course_friction}
            for surface in support['layout']['surfaces'] if int(surface['role'].split('_')[-1]) >= args.friction_start_station}
        support['friction_variation'] = {'version':'spatial_friction_v1', 'start_station':args.friction_start_station, 'authored_friction':args.course_friction, 'combine_mode':'average', 'scope':'Authored pad material; effective robot-pad friction is not directly measured'}
    if args.mapped_contact_progress and ((support or {}).get('mode')!='course' or args.chain_hops not in range(2,9) or args.restore_transition):
        p.error('Mapped contact progression requires an original course evaluation')
    if args.chain_hops is not None and args.chain_hops > 4 and not args.map_course_boundary:
        p.error('Extended courses require the explicit map boundary contract')
    plan = None
    if args.map_goal_forward_m is not None:
        if args.support_mode != 'course' or args.chain_hops not in range(2,9):
            p.error('Geometric execution requires a course with two to eight hops')
        from parkour.geometric_planner import plan_stances
        plan = plan_stances(support['layout'], support['calibration']['foot_xy_m'], args.map_goal_forward_m, max_hops=args.chain_hops, max_step_height_m=.03 if args.course_station_heights is not None else None)
        selected = [c['forward_m'] for c in plan['contacts']]
        expected = [.15*(i+1) for i in range(args.chain_hops)]
        if args.course_step_lengths is not None:
            import itertools
            expected = list(itertools.accumulate(args.course_step_lengths))
        if plan['status'] != 'planned' or (len(selected)!=args.chain_hops or any(abs(x-expected[i])>1e-7 for i,x in enumerate(selected))):
            p.error('No geometric plan compatible with the declared translation sequence')
        for episode in manifest['episodes']:
            episode['foot_offsets_xy_m'] = [[selected[0], 0.] for _ in range(4)]
            if args.course_step_lengths is not None:
                episode['goal_forward_m'] = selected[0]
        manifest['geometric_plan'] = plan
    boundary = None
    if args.map_course_boundary:
        if plan is None or args.restore_transition:
            p.error('Map boundary requires an original geometric course evaluation')
        bounds = [surface['bounds_xy_m'] for surface in support['layout']['surfaces']]
        boundary = {'version': 'map_envelope_v1', 'margin_m': .2,
                    'bounds_xy_m': [min(b[0] for b in bounds)-.2, max(b[1] for b in bounds)+.2,
                                    min(b[2] for b in bounds)-.2, max(b[3] for b in bounds)+.2],
                    'scope': 'root XY outer envelope; foot support and collision checks unchanged'}
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
        if args.support_mode=='full-gap':
            meta['chain_contract']['progress_criterion']='full_platform_gap_v1'
            meta['chain_contract']['physical_gap_width_m']=support['layout']['gap_width_m']
        if args.mapped_contact_progress:
            meta['chain_contract']['progress_criterion']='mapped_contact_v1'
        if args.course_station_heights is not None:
            chosen_heights=[0.]+[c['support_height_m'] for c in plan['contacts']]
            if any(abs(a-b)>1e-7 for a,b in zip(chosen_heights,args.course_station_heights)):
                raise ValueError('Planned heights disagree with generated stations')
            meta['chain_contract']['support_heights_m']=chosen_heights
            meta['chain_contract']['height_contract']='launch_and_landing_surface_relative_v1'
        if args.course_step_lengths is not None:
            meta['chain_contract']['absolute_forward_targets_m'] = selected
            meta['chain_contract']['step_lengths_m'] = args.course_step_lengths
            meta['chain_contract']['spacing_contract'] = 'nonuniform_horizontal_v1'
        if boundary is not None:
            meta['chain_contract']['root_boundary'] = boundary
        manifest['chain_contract'] = meta['chain_contract']
    if plan is not None:
        atomic_json(args.out/'geometric-plan.json', plan)
        meta['geometric_plan'] = plan
        meta['chain_contract']['target_source'] = 'geometric-plan.json contacts; Tracker-compatible translation path'
    if support:
        meta['evaluation_support'] = support
        atomic_json(args.out/'terrain.json', support)
    if args.curriculum_map is not None:
        meta['curriculum_map_override']=json.loads(args.curriculum_map)
    if args.shared_course_level is not None:
        meta['shared_course_override']={'level':args.shared_course_level,'geometry_seed':args.shared_course_seed,
            'scope':'Frozen policy, evaluation-only geometry; training configuration unchanged'}
    if distance_change is not None:meta["evaluation_distance_override"] = distance_change
    recorder = None
    candidate_contract = None
    prefix_replay = None
    planner_state_recorder = None
    try:
        launch_app(args.video)
        import numpy as np
        import torch
        from parkour.learning import make_env, make_algorithm, read_checkpoint, restore
        torch.manual_seed(10000)
        env = make_env(config, evaluation_support=support, chain_hops=args.chain_hops,
                       chain_settle_mode=args.chain_settle_mode, independent_support_clones=args.independent_support_clones, mapped_contact_progress=args.mapped_contact_progress)
        if args.four_step_candidate_probe:
            if config['task']!='a1_continuous_tracker_v1' or args.baseline!='policy' or args.terminal_policy or args.terminal_pose_hold:
                raise ValueError('Candidate probe requires unmodified continuous Tracker policy')
            from parkour.candidate_plan import install_candidates
            if args.candidate_prefix_run:
                from parkour.prefix_replay import PrefixReplay
                prefix_replay=PrefixReplay(env,args.candidate_prefix_run,args.candidate_prefix_steps,args.checkpoint,config)
            else:
                candidate_contract=install_candidates(env)
                meta['candidate_plan_contract']=candidate_contract
        if args.thesis_policy:
            if not 0<args.thesis_action_limit<=4:raise ValueError('Invalid teacher action limit')
            env.cfg.action_limit=args.thesis_action_limit
            meta['evaluation_action_limit']=args.thesis_action_limit
        if args.vectorized_map_contact:
            if not args.mapped_contact_progress:
                raise ValueError('Vectorized map gate requires mapped-contact progression')
            env.vectorized_map_contact=True
            meta['mapped_contact_implementation']='vectorized_immutable_bounds_v1'
        if args.course_station_heights is not None:
            env.planned_support_heights=chosen_heights
        if args.course_step_lengths is not None:
            env.planned_step_lengths = args.course_step_lengths
        if boundary is not None:
            env.course_root_bounds = boundary['bounds_xy_m']
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
            if args.chain_hops not in range(2,9):
                raise ValueError('Transition states require a multi-hop evaluation')
            env.capture_transition_states = True
        alg, norm = make_algorithm(config, env)
        if config.get('reset_jitter'):
            meta['evaluation_initialization']={'training_jitter':config['reset_jitter'],'evaluation_jitter':None,'contract':'fixed initial stance; training-only jitter disabled by evaluation support override'}
        from parkour.learning import model_profile
        meta['model_profile']=model_profile(config,alg,norm,env)
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
        teacher=None
        if args.thesis_policy:
            from parkour.thesis_teacher import ThesisVelocityTeacher
            teacher=ThesisVelocityTeacher(env,args.thesis_policy,args.thesis_source,args.thesis_speed)
            meta['teacher_policy']=teacher.metadata
            meta['model_profile']={'source':'external_user_thesis_policy','policy_parameters':teacher.metadata['policy_parameter_count']}
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
        if config['task']=='a1_continuous_tracker_v1':
            atomic_json(args.out/'target-script.json',env.target_script)
            manifest['target_script']=env.target_script
            meta['stance_calibration']=env.calibration
            offsets=torch.zeros(env.num_envs,4,2,device=env.device)
        else:
            offsets = torch.tensor([episode["foot_offsets_xy_m"] for episode in manifest["episodes"]], device=env.device)
        if hasattr(env, 'set_sequence_offsets'):
            orders=None
            if 'episode_order_indices' in manifest['episodes'][0]:
                orders=torch.tensor([e['episode_order_indices'] for e in manifest['episodes']],device=env.device)
            env.set_sequence_offsets(offsets,episode_orders=orders)
            if config.get('jump'):
                env.required_apex[:]=torch.tensor([e['required_apex_m'] for e in manifest['episodes']],device=env.device)
            meta['stance_calibration'] = env.calibration
        elif config['task']!='a1_continuous_tracker_v1':
            env.targets[:, :, :2] = env.scene.env_origins[:, None, :2] + env.nominal_xy + offsets
        atomic_json(args.out / "scenarios.json", manifest)
        meta["scenario_sha256"] = sha256(args.out / "scenarios.json")
        meta["baseline"] = "thesis-velocity" if teacher is not None else args.baseline
        meta["nominal_foot_xy_m"] = env.nominal_xy.tolist()
        if args.restore_transition:
            if args.chain_hops not in range(2,9) or args.transition_states or args.action_mode != 'mean':
                raise ValueError('Restore probe requires a compatible multi-hop mean policy without nested capture')
            from parkour.transition_states import restore_transition_states
            restored = restore_transition_states(env, args.restore_transition, args.checkpoint, support)
            meta['transition_restore'] = restored
            manifest['transition_restore'] = restored
            atomic_json(args.out/'transition-restore.json', restored)
            atomic_json(args.out/'scenarios.json', manifest)
            meta['scenario_sha256'] = sha256(args.out/'scenarios.json')
        if args.course_step_lengths is not None:
            env.goal_distance[:] = args.course_step_lengths[0]
        if args.course_station_heights is not None:
            env._apply_planned_target_height(env.robot._ALL_INDICES)
        raw = env._get_observations()["policy"]
        done = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        action_clips=torch.zeros(env.num_envs,dtype=torch.long,device=env.device)
        action_values=torch.zeros_like(action_clips)
        action_peak=torch.zeros(env.num_envs,device=env.device)
        terminal_policy=None
        terminal_pose=None
        if args.terminal_pose_hold:
            if args.terminal_policy or config['task']!='a1_continuous_tracker_v1':raise ValueError('Pose hold requires continuous Tracker and no secondary policy')
            from parkour.terminal_pose import TerminalPoseHold
            terminal_pose=TerminalPoseHold(env,args.terminal_pose_mode)
            meta['terminal_pose_hold']=terminal_pose.metadata
        if args.terminal_policy:
            from parkour.terminal_policy import TerminalPolicy
            terminal_policy=TerminalPolicy(args.terminal_policy,config,env)
            meta['terminal_policy']=terminal_policy.metadata
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
            if config['task']=='a1_continuous_tracker_v1':
                from parkour.continuous_diagnostics import ContinuousDiagnostics
                diagnostics=ContinuousDiagnostics(env,done)
            else:
                diagnostics = MotionDiagnostics(env, done)
        if args.video:
            from parkour.media import ParallelRecorder
            if (args.video_camera_mode or config.get('evaluation_camera_mode'))=='follow':
                from parkour.media import FollowRecorder
                recorder=FollowRecorder(env,args.out,env_index=args.video_follow_env_index)
            else:
                recorder = ParallelRecorder(env,args.out,count=args.video_envs,camera_side=args.video_camera_side)
        if diagnostics and config['task']=='a1_continuous_tracker_v1' and args.checkpoint and not (args.four_step_candidate_probe or args.thesis_policy or args.terminal_policy or args.terminal_pose_hold):
            from parkour.planner_states import PlannerStateRecorder
            state_config=dict(config)
            if meta.get('evaluation_support'):state_config['terrain_contract']=meta['evaluation_support']
            planner_state_recorder=PlannerStateRecorder(env,state_config,sha256(args.checkpoint))
        with torch.inference_mode():
            for step in range(env.max_episode_length + 1):
                if planner_state_recorder is not None:planner_state_recorder.capture(step,done)
                if prefix_replay is not None and step==prefix_replay.steps:
                    valid=prefix_replay.validate()
                    atomic_json(args.out/'prefix-validation.json',prefix_replay.metadata)
                    if not valid:raise RuntimeError('Prefix replay diverged; candidate execution rejected')
                    from parkour.candidate_plan import install_candidates
                    start=int(env.progress.target[:,0].max())
                    candidate_contract=install_candidates(env,start)
                    meta['candidate_plan_contract']=candidate_contract
                    meta['prefix_replay']=prefix_replay.metadata
                    raw=env._get_observations()['policy']
                if teacher is not None:
                    action=teacher.act()
                elif args.baseline == "zero":
                    action = torch.zeros(env.num_envs, 12, device=env.device)
                else:
                    policy_obs = raw.clone()
                    if args.baseline == "shuffled-target":
                        # Replace only target channels; the true task/reward remains unchanged.
                        policy_obs[:, 45:57] = torch.roll(policy_obs[:, 45:57], 1, dims=0)
                    normalized = norm(policy_obs)
                    action = (sample_action(alg.policy, normalized, action_rng) if args.action_mode == 'sampled'
                              else alg.policy.act_inference(normalized))
                if prefix_replay is not None and step<prefix_replay.steps:
                    action=prefix_replay.action(step)
                if terminal_policy is not None:
                    action=terminal_policy.apply(raw,action,step,done)
                if terminal_pose is not None:action=terminal_pose.apply(raw,action,step,done)
                action_clips+=((action.abs()>env.cfg.action_limit)&~done[:,None]).sum(1)
                action_values+=(~done).long()*action.shape[1]
                action_peak=torch.where(~done,torch.maximum(action_peak,action.abs().amax(1)),action_peak)
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
                    records[index]['input_action_clip_fraction']=float(action_clips[index])/max(1,int(action_values[index]))
                    records[index]['input_action_abs_peak']=float(action_peak[index])
                    if terminal_pose is not None:
                        records[index]['terminal_pose_used']=bool(terminal_pose.latched[index])
                        records[index]['terminal_pose_handoff_time_s']=float(terminal_pose.steps[index])*env.step_dt if terminal_pose.latched[index] else None
                    if terminal_policy is not None:
                        records[index]['terminal_policy_used']=bool(terminal_policy.latched[index])
                        records[index]['terminal_policy_handoff_time_s']=float(terminal_policy.steps[index])*env.step_dt if terminal_policy.latched[index] else None
                    if 'active_foot' in manifest['episodes'][index]:
                        records[index]['active_foot']=manifest['episodes'][index]['active_foot']
                done |= newly_done
                if bool(done.all()):
                    break
        if not bool(done.all()) or any(record is None for record in records):
            raise RuntimeError("Evaluation incomplete; missing scenario results")
        if recorder:
            recorder.close(episode=records[recorder.ids[0]], selection=args.video_selection_reason or 'fixed first environment; not selected for success', episodes=[records[i] for i in recorder.ids],
                           recording_kind=('single_robot_follow_evaluation' if (args.video_camera_mode or config.get('evaluation_camera_mode'))=='follow' else 'parallel_evaluation'),
                           video_stop_rule=('followed first episode only; recording ends on its termination' if (args.video_camera_mode or config.get('evaluation_camera_mode'))=='follow' else 'last visible first episode; subsequent auto-resets shown but excluded from metrics'))
            recorder = None
        if planner_state_recorder is not None:planner_state_recorder.close(args.out)
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
        if teacher is not None:
            meta['teacher_policy']['action_clip_fraction']=teacher.clipped/max(1,teacher.total)
        if config['task']=='a1_continuous_tracker_v1':
            report.update(success_contract='continuous_front_rear_targets_v1 + final shared-platform support and stabilization',
                success_wilson95=None,success_interval_note='Fixed course and initial state replicas, not independent terrain samples',
                mean_front_accepted_index=sum(r['front_accepted_index'] for r in records)/count,
                mean_rear_accepted_index=sum(r['rear_accepted_index'] for r in records)/count,
                required_final_index=len(support['layout']['surfaces'])-1,
                evaluation_scope='Frozen thesis velocity policy; does not consume scripted foothold targets' if teacher is not None else 'Scripted contact buffer; not autonomous map planning')
            report['pair_contact_quorum']=env.cfg.pair_contact_quorum
            report['input_action_clip_fraction']=float(action_clips.sum())/max(1,int(action_values.sum()))
            report['input_action_diagnostic_scope']='Actions submitted to environment before its configured clamp; does not measure torque saturation'
            if terminal_policy is not None:report['terminal_policy']=terminal_policy.metadata
            if terminal_pose is not None:
                report['terminal_pose_hold']=terminal_pose.metadata
                report['evaluation_scope']+='; explicit calibrated terminal pose hold, not pure RL stabilization'
            report['planned_gap_count']=support['layout'].get('planned_gap_count')
            report['planned_gap_widths_m']=[g['projected_top_gap_m'] for g in support['layout'].get('gap_locations',[])]
            report['initial_rear_target']=env.cfg.initial_rear_target
            report['contact_body_names']=env.contacts.body_names
            report['evaluation_contact_radius_m']=env.cfg.success_radius_m
            report['contact_target_mode']=env.cfg.contact_target_mode
            if env.cfg.contact_target_mode=='surface_region':
                report['evaluation_contact_radius_m']=None
                report['contact_region_contract']='selected exposed shared top; 2cm edge margin; normal offset 0..4cm; normal force>5N; geometric attribution'
            report['mean_measured_jump_count']=sum(r.get('measured_jump_count',0) for r in records)/count
            report['mean_clean_airborne_count']=sum(r.get('clean_airborne_count',0) for r in records)/count
            report['mean_travel_clean_airborne_count']=sum(r.get('travel_clean_airborne_count',0) for r in records)/count
            report['mean_travel_measured_jump_count']=sum(r.get('travel_measured_jump_count',0) for r in records)/count
            report['airborne_count_contract']='All feet below 2N >=20ms, then foot recontact, no nonfoot force >5N during flight; includes low running bounds and drops, not necessarily a gap crossing'
            report['measured_jump_contract']='Clean airborne event plus root rise >=3cm and world vertical velocity >0.2m/s; unchanged strict criterion'
            if env.gap_credit is not None:
                report['mean_credited_gap_jumps']=sum(r['credited_gap_jumps'] for r in records)/count
                report['gap_jump_credit_contract']='Valid forward flight >= half projected gap width, followed by both pair acceptance; once per gap; reward diagnostic, not independent collision-pair attribution'
            report['mean_active_motion_seconds']=sum(r.get('active_motion_seconds',0) for r in records)/count
            report['active_motion_contract']='200Hz body linear speed norm >0.15m/s; accumulated moving time, excludes stationary waiting'
            report['mean_travel_motion_seconds']=sum(r.get('travel_motion_seconds',0) for r in records)/count
            report['travel_motion_contract']='Speed norm >0.15m/s before both pair targets become final stance; excludes terminal rocking/settling'
            report['mean_completed_surface_transfers']=sum(r.get('completed_surface_transfers',0) for r in records)/count
            if config.get('demo_target'):
                target=dict(config['demo_target'])
                target['minimum_measured_jumps']=target.get('minimum_measured_jumps',8)
                target['eligibility_contract']='dynamic_long_course_v5'
                target['minimum_travel_motion_seconds']=target.get('minimum_travel_motion_seconds',10.)
                report['demo_eligible_scenario_ids']=[r['scenario_id'] for r in records if r['success'] and r['length']*env.step_dt>=target['minimum_actual_seconds'] and r.get('travel_motion_seconds',0)>=target['minimum_travel_motion_seconds'] and r.get('completed_surface_transfers',0)>=target['surface_transfers'] and r.get('travel_measured_jump_count',0)>=target['minimum_measured_jumps']]
                report['demo_target']=target
                report['followed_video_demo_eligible']=records[args.video_follow_env_index]['scenario_id'] in report['demo_eligible_scenario_ids']
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
            if args.course_step_lengths is None:
                report['by_distance'] = by_distance(records, manifest['episodes'])
            else:
                from parkour.evaluation_summary import validate_course_distances
                validate_course_distances(records, manifest['episodes'], args.course_step_lengths)
                report['by_distance'] = None
                report['distance_summary_scope'] = 'Nonuniform course: per-hop targets and outcomes in chain-events.json'
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
        if args.support_mode=='full-gap':
            report['success_contract']='last preflight contacts on departure platform + legacy launch/body-travel/precision/stability gates + first and final foot support on landing platform'
            report['evaluation_scope']='full_platform_gap_v1; fixed one-hop target, not planner navigation'
        if args.mapped_contact_progress:
            report['success_contract']='valid flight + launch region + first contact on assigned surface + precise stable support; trunk airborne distance is a separate legacy metric'
            report['evaluation_scope']='mapped_contact_v1; not comparable to legacy strict-travel success'
        if args.restore_transition:
            report['evaluation_scope'] = 'restored_remaining_hop_only'
            report['success_contract'] = 'Remaining hop from restored landing passes original gates; prior hop not executed in this run'
            report['course_successes'] = None
            report['restored_prior_hops'] = 1
            report['hop_diagnostic_scope'] = 'return/errors describe restored segment; length retains source episode clock'
        if candidate_contract is not None:
            groups=[]
            for candidate in range(9):
                rows=[r for i,r in enumerate(records) if candidate_contract['candidate_id_by_environment'][i]==candidate]
                groups.append({'candidate_id':candidate,'episodes':len(rows),
                    'required_surface_index':candidate_contract['start_surface']+3,
                    'candidate_horizon_reached':sum(r['completed_surface_transfers']>=candidate_contract['start_surface']+3 for r in rows),
                    'course_successes':sum(r['success'] for r in rows),
                    'mean_transfers':sum(r['completed_surface_transfers'] for r in rows)/len(rows)})
            atomic_json(args.out/'candidate-rollouts.json',{'contract':candidate_contract,'results':groups,
                'scope':'Reaching the end of the candidate horizon is a prefix metric, not full course success. No real-time or state-clone fidelity claim.'})
            report['evaluation_scope']='four_step_candidate_physical_rollouts'
        atomic_json(args.out / "evaluation.json", report)
        meta["evaluation"] = {key: value for key, value in report.items() if key != "results"}
        meta["artifacts"] = {file.name: sha256(file) for file in args.out.iterdir()
                             if file.suffix in (".mp4", ".png") or file.name in ("planner-states.json", "prefix-validation.json", "candidate-rollouts.json", "transition-restore.json", "transition-states.json", "transition-states.npz", "geometric-plan.json", "collision-contract.json", "terrain.json", "evaluation.json", "scenarios.json", "replay.json", "diagnostics.json", "motion-trace.npz", "reward-components.json", "reward-components.npz")}
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
