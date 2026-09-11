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
    normalizer = EmpiricalNormalization(shape=[obs_dim]).to(env.device)
    return alg, normalizer


def save_checkpoint(path, config, alg, normalizer, env, completed_iterations, total_steps):
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
    if data['config'].get('exploration') != config.get('exploration'):
        raise ValueError('Checkpoint exploration contract differs')
    from parkour.terrain_contract import assert_same_terrain
    assert_same_terrain(data['config'], config)
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


def make_env(config, evaluation_support=None):
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
    elif config['task'] == 'a1_t0_foothold_v1':
        cfg, env_type = FootholdCfg(), FootholdEnv
    else:
        raise ValueError('Unknown task contract')
    cfg.seed = config["seed"]
    cfg.scene.num_envs = config["num_envs"]
    cfg.episode_length_s = config["episode_seconds"]
    for key in ("target_offset_m", "surface_height_m", "success_radius_m", "success_dwell_s"):
        setattr(cfg, key, config[key])
    cfg.sim.device = "cuda:0"
    from parkour.terrain_contract import training_support
    cfg.support_contract = copy.deepcopy(evaluation_support) if evaluation_support is not None else training_support(config)
    return env_type(cfg)
