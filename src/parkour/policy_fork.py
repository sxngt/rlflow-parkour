"""Explicit policy initialization for a new terrain experiment, never a resume."""
import copy
import math
import torch
from parkour.exploration import cap_for_update
from parkour.terrain_contract import training_support


def validate_fork_configs(parent, target):
    if parent.get('task') == 'a1_continuous_tracker_v1':
        return validate_continuous_fork(parent, target)
    from parkour.support_assignment import support_assignment
    support_assignment(parent); support_assignment(target)
    from parkour.chain_training import validate_chain_training
    validate_chain_training(parent); validate_chain_training(target)
    training_support(parent); training_support(target)
    from parkour.observation_contract import validate_history
    old_history,new_history=validate_history(parent),validate_history(target)
    if old_history is not None and old_history!=new_history:
        raise ValueError('Fork cannot reinterpret an existing history policy')
    a,b=copy.deepcopy(parent),copy.deepcopy(target)
    if a['task']!='a1_directed_jump_v5' or b['task']!=a['task']:
        raise ValueError('Fork supports directed-jump policies only')
    for c in (a,b):
        c.pop('observation_history', None)
        c.pop('support_assignment', None)
        c.pop('retention_training', None)  # Strictly validated above; new task mixture is a fork.
        if c.pop('chain_training', None) is not None:
            c['episode_seconds'] = 4.  # Only the validated eight-second chain is normalized.
        for key in ('iterations','num_envs','research_tags'):
            c.pop(key,None)
        for key in ('train_forward_range_m','train_forward_choices_m','evaluation_forward_m','distance_curriculum','launch_curriculum'):
            c['jump'].pop(key,None)
        for key in ('mode','layout','friction_variation','surface_material_overrides'):
            c['terrain_contract'].pop(key,None)
        c['exploration'].pop('stages',None)
    if a!=b:
        raise ValueError('Fork changed an unsupported robot, observation, reward, seed or optimizer contract')
    if parent['terrain_contract']['mode'] not in ('continuous','split','deck','course') or target['terrain_contract']['mode'] not in ('continuous','split','deck','course'):
        raise ValueError('Fork terrain change is not supported')
    cap_for_update(target,0)


def validate_continuous_fork(parent, target):
    """Allow explicit terrain, contact, reward-reference and exploration variants.

    Robot limits, input channels and network tensors remain compatible; an
    exploration-kind change can alter the actor function despite copied weights.
    """
    from parkour.contact_curriculum import radius_for_update
    if target.get('task') != parent['task']:
        raise ValueError('Continuous fork cannot change task')
    a,b=copy.deepcopy(parent),copy.deepcopy(target)
    for config in (a,b):
        from parkour.reset_jitter import validate_jitter
        validate_jitter(config);config.pop("reset_jitter",None)
        from parkour.gap_clearance import validate_clearance
        validate_clearance(config)
        config.pop("gap_clearance",None)
        from parkour.motion_control import validate_motion
        validate_motion(config)
        config.pop("motion_control",None)
        terminal_cost=config.pop('terminal_motion_cost',0.)
        if not isinstance(terminal_cost,(int,float)) or not math.isfinite(terminal_cost) or not 0<=terminal_cost<=10:
            raise ValueError('Invalid terminal motion cost')
        bonus=config.pop('gap_jump_bonus',0.)
        if not isinstance(bonus,(int,float)) or not math.isfinite(bonus) or not 0<=bonus<=20:
            raise ValueError('Invalid gap jump bonus')
        if config.pop('body_progress_reference','pair_midpoint') not in ('pair_midpoint','gap_landing'):
            raise ValueError('Invalid body progress reference')
        learning_rate=config['runner']['algorithm'].pop('learning_rate')
        if not isinstance(learning_rate,(int,float)) or not math.isfinite(learning_rate) or not 0<learning_rate<=.01:
            raise ValueError('Invalid explicit fork learning rate')
        if config.pop('bound_reward_scope','all') not in ('all','travel_only'):
            raise ValueError('Invalid bound reward scope')
        mode=config.pop('contact_target_mode','point')
        if mode not in ('point','surface_region'):
            raise ValueError('Invalid contact target mode')
        if mode=='surface_region' and config.get('contact_curriculum') is not None:
            raise ValueError('Region fork cannot use point precision curriculum')
        support=training_support(config)
        if support is None or support['mode']!='shared-course':
            raise ValueError('Continuous fork requires validated shared terrain')
        if cap_for_update(config,0) is None:
            raise ValueError('Continuous fork requires bounded exploration')
        config['exploration'].pop('kind')
        # 2026-09-15: 탐색 std 하한(min_std)도 fork 변형으로 허용. 성숙한 정책의 미세조정은 더 낮은 노이즈가 필요하다 (stochastic rollout 붕괴 완화).
        config['exploration'].pop('min_std',None)
        radius_for_update(config,0)
        for key in ('iterations','num_envs','research_tags','contact_curriculum'):
            config.pop(key,None)
        for key in ('layout','geometry_seed','terrain_mix'):
            config['terrain_contract'].pop(key,None)
        # Apart from variants validated above, retain the std floor, network,
        # observation channels, actuator envelope and reward weights.
        config['exploration'].pop('stages',None)
    if a!=b:
        raise ValueError('Continuous fork changed robot, observation, action, reward, seed or evaluation contract')


def initialize_fork(data, config, alg, normalizer):
    validate_fork_configs(data['config'],config)
    if alg.optimizer.state:
        raise ValueError('Fork requires a fresh optimizer')
    # Validate both state dictionaries completely before copying either one.
    states={}
    for module,key in ((alg.policy,'model'),(normalizer,'normalizer')):
        expected=module.state_dict();source=dict(data[key])
        if key=='model' and config.get('observation_history') is not None and data['config'].get('observation_history') is None:
            for name in ('actor.0.weight','critic.0.weight'):
                old=source[name]
                if old.shape!=(expected[name].shape[0],66):
                    raise ValueError('History initialization requires the original 66-channel policy')
                extended=torch.zeros_like(expected[name]);extended[:,:66]=old
                source[name]=extended
        if expected.keys()!=source.keys():
            raise ValueError('Fork state keys differ: '+key)
        for name,tensor in source.items():
            if tensor.shape!=expected[name].shape or tensor.dtype!=expected[name].dtype or not torch.isfinite(tensor).all():
                raise ValueError('Incompatible or nonfinite fork tensor: '+key+'.'+name)
        states[key]=source
    alg.policy.load_state_dict(states['model'])
    normalizer.load_state_dict(states['normalizer'])
    # These are distribution controls of the NEW experiment, not learned tensors.
    alg.policy.std_cap.fill_(cap_for_update(config,0))
    alg.policy.std_floor.fill_(config['exploration']['min_std'])
    return {'contract':'policy_critic_normalizer_copy; fresh_optimizer_rng_curriculum; new_episode_boundary',
            'parent_contact_target_mode':data['config'].get('contact_target_mode','point'),
            'contact_target_mode':config.get('contact_target_mode','point'),
            'parent_bound_reward_scope':data['config'].get('bound_reward_scope','all'),
            'bound_reward_scope':config.get('bound_reward_scope','all'),
            'parent_body_progress_reference':data['config'].get('body_progress_reference','pair_midpoint'),
            'body_progress_reference':config.get('body_progress_reference','pair_midpoint'),
            'parent_gap_jump_bonus':data['config'].get('gap_jump_bonus',0.),
            'gap_jump_bonus':config.get('gap_jump_bonus',0.),
            'parent_reset_jitter':data['config'].get('reset_jitter'),'reset_jitter':config.get('reset_jitter'),
            'parent_gap_clearance':data['config'].get('gap_clearance'),
            'gap_clearance':config.get('gap_clearance'),
            'parent_motion_control':data['config'].get('motion_control'),
            'motion_control':config.get('motion_control'),
            'parent_terminal_motion_cost':data['config'].get('terminal_motion_cost',0.),
            'terminal_motion_cost':config.get('terminal_motion_cost',0.),
            'initial_learning_rate':alg.learning_rate,
            'initial_actor_function_preserved':data['config'].get('exploration',{}).get('kind')==config.get('exploration',{}).get('kind'),
            'exploration_contract':config.get('exploration',{}).get('kind'),
            'parent_completed_iterations':data['completed_iterations'],
            'parent_environment_steps':data['total_environment_steps'],
            'initial_completed_iterations':0,'initial_environment_steps':0,
            'initial_std_cap':cap_for_update(config,0),
            'history_initialization':'zero extra actor/critic input columns; shared current-frame normalization' if config.get('observation_history') is not None and data['config'].get('observation_history') is None else None}
