"""Explicit policy initialization for a new terrain experiment, never a resume."""
import copy
import torch
from parkour.exploration import cap_for_update
from parkour.terrain_contract import training_support


def validate_fork_configs(parent, target):
    training_support(parent); training_support(target)
    a,b=copy.deepcopy(parent),copy.deepcopy(target)
    if a['task']!='a1_directed_jump_v5' or b['task']!=a['task']:
        raise ValueError('Fork supports directed-jump policies only')
    for c in (a,b):
        for key in ('iterations','num_envs','research_tags'):
            c.pop(key,None)
        for key in ('train_forward_range_m','evaluation_forward_m','distance_curriculum','launch_curriculum'):
            c['jump'].pop(key,None)
        for key in ('mode','layout'):
            c['terrain_contract'].pop(key,None)
        c['exploration'].pop('stages',None)
    if a!=b:
        raise ValueError('Fork changed an unsupported robot, observation, reward, seed or optimizer contract')
    if parent['terrain_contract']['mode']!='continuous' or target['terrain_contract']['mode'] not in ('continuous','split'):
        raise ValueError('Fork terrain change is not supported')
    cap_for_update(target,0)


def initialize_fork(data, config, alg, normalizer):
    validate_fork_configs(data['config'],config)
    if alg.optimizer.state:
        raise ValueError('Fork requires a fresh optimizer')
    # Validate both state dictionaries completely before copying either one.
    for module,key in ((alg.policy,'model'),(normalizer,'normalizer')):
        expected=module.state_dict();source=data[key]
        if expected.keys()!=source.keys():
            raise ValueError('Fork state keys differ: '+key)
        for name,tensor in source.items():
            if tensor.shape!=expected[name].shape or tensor.dtype!=expected[name].dtype or not torch.isfinite(tensor).all():
                raise ValueError('Incompatible or nonfinite fork tensor: '+key+'.'+name)
    alg.policy.load_state_dict(data['model'])
    normalizer.load_state_dict(data['normalizer'])
    # These are distribution controls of the NEW experiment, not learned tensors.
    alg.policy.std_cap.fill_(cap_for_update(config,0))
    alg.policy.std_floor.fill_(config['exploration']['min_std'])
    return {'contract':'policy_critic_normalizer_copy; fresh_optimizer_rng_curriculum; new_episode_boundary',
            'parent_completed_iterations':data['completed_iterations'],
            'parent_environment_steps':data['total_environment_steps'],
            'initial_completed_iterations':0,'initial_environment_steps':0,
            'initial_std_cap':cap_for_update(config,0)}
