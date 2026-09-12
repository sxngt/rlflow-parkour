"""Fixed PPO implementation adapter; no off-policy trajectory replay."""
from __future__ import annotations

import copy
import random
from pathlib import Path
import numpy as np
import torch
from rsl_rl.algorithms import PPO
from rsl_rl.modules import ActorCritic, EmpiricalNormalization
from parkour.runtime import sha256, atomic_json
from parkour.launch_curriculum import checkpoint_state


def make_algorithm(config, env):
    policy_cfg = copy.deepcopy(config["runner"]["policy"])
    if policy_cfg.pop("class_name") != "ActorCritic":
        raise ValueError("Only ActorCritic is supported")
    obs_dim = env.cfg.observation_space
    if config.get('exploration') is not None:
        from parkour.exploration import BoundedActorCritic, cap_for_update
        policy = BoundedActorCritic(obs_dim, obs_dim, 12,
            min_std=config['exploration']['min_std'], max_std=cap_for_update(config,0), **policy_cfg).to(env.device)
    else:
        policy = ActorCritic(obs_dim, obs_dim, 12, **policy_cfg).to(env.device)
    alg_cfg = copy.deepcopy(config["runner"]["algorithm"])
    if alg_cfg.pop("class_name") != "PPO":
        raise ValueError("Only PPO is supported")
    alg = PPO(policy, device=env.device, **alg_cfg)
    alg.init_storage("rl", env.num_envs, config["runner"]["num_steps_per_env"], [obs_dim], [obs_dim], [12])
    from parkour.observation_contract import validate_history
    history_spec=validate_history(config)
    if history_spec is None:
        normalizer = EmpiricalNormalization(shape=[obs_dim]).to(env.device)
    else:
        from parkour.observation_history import HistoryNormalization
        normalizer=HistoryNormalization(history_spec).to(env.device)
    return alg, normalizer


def save_checkpoint(path, config, alg, normalizer, env, completed_iterations, total_steps, lineage=None):
    data = {
        "schema_version": 1, "config": config, "completed_iterations": completed_iterations,
        "total_environment_steps": total_steps, "model": alg.policy.state_dict(),
        "optimizer": alg.optimizer.state_dict(), "learning_rate": alg.learning_rate,
        "normalizer": normalizer.state_dict(), "rng_python": random.getstate(),
        "rng_numpy": np.random.get_state(), "rng_torch": torch.get_rng_state(),
        "rng_cuda": torch.cuda.get_rng_state_all(), "rng_scenario": env.generator.get_state(),
        "curriculum": checkpoint_state(config, completed_iterations),
        "resume_contract": "new_episode_boundary; unfinished episodes discarded; not bitwise replay",
    }
    if lineage is not None:data["lineage"] = copy.deepcopy(lineage)
    path = Path(path)
    temp = path.with_suffix(".tmp")
    torch.save(data, temp)
    # Validate readability before marking the artifact complete.
    check = torch.load(temp, map_location="cpu", weights_only=False)
    assert check["completed_iterations"] == completed_iterations
    temp.replace(path)
    atomic_json(path.with_suffix(".json"), {"sha256": sha256(path), "bytes": path.stat().st_size,
        "completed_iterations": completed_iterations, "total_environment_steps": total_steps})


def read_checkpoint(path):
    path = Path(path)
    import json
    sidecar = json.loads(path.with_suffix(".json").read_text())
    if sha256(path) != sidecar["sha256"]:
        raise ValueError("Checkpoint hash mismatch")
    # Only locally generated trusted checkpoints. torch pickle is not a public upload format.
    return torch.load(path, map_location="cpu", weights_only=False)


def restore(data, config, alg, normalizer, env, training):
    if data['config'].get('contact_target_mode','point') != config.get('contact_target_mode','point'):
        raise ValueError('Checkpoint contact target mode differs; not a resume')
    from parkour.support_assignment import assert_same_support_assignment
    assert_same_support_assignment(data['config'], config)
    from parkour.chain_training import assert_same_chain_training
    assert_same_chain_training(data['config'], config)
    if data['config'].get('pair_contact_quorum','both') != config.get('pair_contact_quorum','both'):
        raise ValueError('Checkpoint contact quorum differs')
    if data['config'].get('initial_rear_target','own_stance') != config.get('initial_rear_target','own_stance'):
        raise ValueError('Checkpoint initial rear target contract differs')
    if data['config'].get('action_limit',1.) != config.get('action_limit',1.):
        raise ValueError('Checkpoint action limit differs')
    if data['config'].get('bound_reward_per_second',0.) != config.get('bound_reward_per_second',0.):
        raise ValueError('Checkpoint bounding reward differs')
    if data['config'].get('body_progress_weight',0.) != config.get('body_progress_weight',0.):
        raise ValueError('Checkpoint body progress reward differs')
    if data['config'].get('contact_curriculum') != config.get('contact_curriculum'):
        raise ValueError('Checkpoint contact curriculum differs')
    if data['config'].get('exploration') != config.get('exploration'):
        raise ValueError('Checkpoint exploration contract differs')
    from parkour.terrain_contract import assert_same_terrain
    assert_same_terrain(data['config'], config)
    from parkour.observation_contract import validate_history
    if validate_history(data['config']) != validate_history(config):
        raise ValueError('Checkpoint observation history contract differs')
    keys = ("task", "episode_seconds", "target_offset_m", "surface_height_m", "success_radius_m", "success_dwell_s", "runner")
    if any(data["config"][key] != config[key] for key in keys):
        raise ValueError("Checkpoint/task contract differs")
    if data['config'].get('jump') != config.get('jump'):
        raise ValueError('Checkpoint jump contract differs')
    if data['config'].get('sequence') != config.get('sequence'):
        raise ValueError('Checkpoint sequence contract differs')
    if training and data.get("curriculum") != checkpoint_state(config, data["completed_iterations"]):
        raise ValueError("Checkpoint curriculum state differs")
    alg.policy.load_state_dict(data["model"])
    normalizer.load_state_dict(data["normalizer"])
    if training:
        if data["config"]["num_envs"] != config["num_envs"] or data["config"]["seed"] != config["seed"]:
            raise ValueError("Resume must keep seed and environment count")
        alg.optimizer.load_state_dict(data["optimizer"])
        alg.learning_rate = data["learning_rate"]
        random.setstate(data["rng_python"])
        np.random.set_state(data["rng_numpy"])
        torch.set_rng_state(data["rng_torch"])
        torch.cuda.set_rng_state_all(data["rng_cuda"])
        env.generator.set_state(data["rng_scenario"])


def make_env(config, evaluation_support=None, chain_hops=None, chain_settle_mode='default', independent_support_clones=False, mapped_contact_progress=None):
    from parkour.chain_training import validate_chain_training
    chain_spec = validate_chain_training(config)
    retention = (config.get('retention_training') is not None and chain_hops is None
                 and evaluation_support is None)
    from parkour.task import FootholdCfg, FootholdEnv
    if config['task'] in ('a1_flat_jump_v1','a1_flat_jump_shaped_v2','a1_flat_jump_precise_v3','a1_flat_jump_supported_v4','a1_directed_jump_v5'):
        from parkour.jump_task import JumpCfg,JumpEnv
        cfg,env_type=JumpCfg(),JumpEnv
        if config['task'] in ('a1_flat_jump_precise_v3','a1_flat_jump_supported_v4','a1_directed_jump_v5'):
            from parkour.precision_jump_task import PrecisionJumpEnv
            env_type=PrecisionJumpEnv
        if config['task']=='a1_directed_jump_v5':
            from parkour.directed_jump_task import DirectedJumpEnv
            env_type=DirectedJumpEnv
        cfg.sequence=copy.deepcopy(config['sequence']);cfg.jump=copy.deepcopy(config['jump'])
    elif config['task'] in ('a1_t0_sequential_v2','a1_t0_sequential_stable_v3','a1_t0_single_foot_v4','a1_t0_single_foot_aligned_v5','a1_t0_single_foot_continuous_v6','a1_t0_shared_single_foot_v7'):
        from parkour.sequential_task import SequentialCfg, SequentialEnv
        if config['surface_height_m'] != 0:
            raise ValueError('Sequential v2 currently supports flat ground only')
        cfg, env_type = SequentialCfg(), SequentialEnv
        cfg.sequence = copy.deepcopy(config['sequence'])
        if config['task'] in ('a1_t0_sequential_stable_v3','a1_t0_single_foot_v4','a1_t0_single_foot_aligned_v5','a1_t0_single_foot_continuous_v6','a1_t0_shared_single_foot_v7'):
            from parkour.stable_task import StableSequentialEnv
            env_type=StableSequentialEnv
    elif config['task']=='a1_continuous_tracker_v1':
        from parkour.continuous_tracker_task import ContinuousTrackerCfg,ContinuousTrackerEnv
        cfg,env_type=ContinuousTrackerCfg(),ContinuousTrackerEnv
        cfg.contact_target_mode=config.get('contact_target_mode','point')
        if cfg.contact_target_mode not in ('point','surface_region'):raise ValueError('Invalid contact target mode')
        if cfg.contact_target_mode=='surface_region' and config.get('contact_curriculum') is not None:
            raise ValueError('Surface regions cannot use point-radius curriculum')
        cfg.scene.env_spacing=14.
        cfg.pair_contact_quorum=config.get('pair_contact_quorum','both')
        if cfg.pair_contact_quorum not in ('both','either'):raise ValueError('Invalid pair quorum')
        cfg.initial_rear_target=config.get('initial_rear_target','own_stance')
        if cfg.initial_rear_target not in ('own_stance','front_stance'):raise ValueError('Invalid initial rear target')
        cfg.bound_reward_per_second=float(config.get('bound_reward_per_second',0.))
        if not 0<=cfg.bound_reward_per_second<=10:raise ValueError('Invalid bound reward rate')
        cfg.body_progress_weight=float(config.get('body_progress_weight',0.))
        if not 0<=cfg.body_progress_weight<=100:raise ValueError('Invalid body progress weight')
    elif config['task'] == 'a1_t0_foothold_v1':
        cfg, env_type = FootholdCfg(), FootholdEnv
    else:
        raise ValueError('Unknown task contract')
    from parkour.observation_contract import validate_history
    history_spec=validate_history(config)
    if history_spec is not None:
        cfg.observation_history=history_spec
        cfg.observation_space=history_spec['frames']*history_spec['base_observation_dim']+history_spec['frames']-1
    cfg.mapped_contact_progress = ((chain_spec or {}).get('progress_criterion') == 'mapped_contact_v1'
                                   if mapped_contact_progress is None else mapped_contact_progress)
    cfg.action_limit=float(config.get("action_limit",1.))
    if not 0<cfg.action_limit<=4:raise ValueError("Invalid normalized action limit")
    cfg.seed = config["seed"]
    cfg.scene.num_envs = config["num_envs"]
    if independent_support_clones:
        if (config.get('support_assignment', {}).get('single_mode') != 'deck'
                or not evaluation_support or evaluation_support['mode'] != 'deck'):
            raise ValueError('Independent clone evaluation requires explicit all-deck support assignment')
    if (retention and config.get('support_assignment') is not None) or independent_support_clones:
        from parkour.support_assignment import support_assignment
        cfg.support_assignment = support_assignment(config)
        cfg.scene.replicate_physics = False
    cfg.episode_length_s = config["episode_seconds"]
    for key in ("target_offset_m", "surface_height_m", "success_radius_m", "success_dwell_s"):
        setattr(cfg, key, config[key])
    cfg.sim.device = "cuda:0"
    from parkour.terrain_contract import training_support
    cfg.support_contract = copy.deepcopy(evaluation_support) if evaluation_support is not None else training_support(config)
    if cfg.support_contract is not None:
        from parkour.terrain_contract import validate_surface_materials
        validate_surface_materials(cfg.support_contract)
        if cfg.support_contract.get('mode') in ('full-gap','shared-course'):
            cfg.sim.enable_scene_query_support=True
    if chain_spec is not None and chain_hops is None:
        chain_hops = chain_spec['hops']
        chain_settle_mode = chain_spec['settle_command']
    if chain_hops is not None:
        if config['task'] != 'a1_directed_jump_v5' or not cfg.support_contract:
            raise ValueError('Chained adapter requires directed jump with explicit support')
        if chain_hops >= 2 and cfg.support_contract['mode'] not in ('deck', 'course'):
            raise ValueError('Two-hop execution requires deck or course support')
        from parkour.chained_jump_task import ChainedDirectedJumpEnv
        cfg.episode_length_s = 4. * chain_hops
        return ChainedDirectedJumpEnv(cfg, hops=chain_hops, settle_mode=chain_settle_mode, retention=retention,
                                      retention_goals=(config.get('retention_training') or {}).get('single_goal_choices_m'),
                                      retention_weights=(config.get('retention_training') or {}).get('single_goal_weights'))
    return env_type(cfg)


def model_profile(config, alg, normalizer, env):
    return {'observation_dimension':env.cfg.observation_space,
            'actor_parameters':sum(p.numel() for p in alg.policy.actor.parameters()),
            'critic_parameters':sum(p.numel() for p in alg.policy.critic.parameters()),
            'total_policy_parameters':sum(p.numel() for p in alg.policy.parameters()),
            'normalization_channels':int(normalizer._mean.shape[-1]),
            'observation_history':config.get('observation_history')}
