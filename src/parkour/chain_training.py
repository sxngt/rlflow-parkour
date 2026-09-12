"""Strict P2-34 chain training contract, distinct from runtime evaluation."""


def validate_chain_training(config):
    spec = config.get('chain_training')
    if spec is None:
        if config.get('retention_training') is not None:
            raise ValueError('Retention mixture requires chain training')
        return None
    expected = {'schema_version': 1, 'hops': 2, 'forward_per_hop_m': .15,
                'hop_seconds': 4., 'settle_command': 'default'}
    course_contract = dict(expected, schema_version=2, settle_command='hold-last')
    mapped3 = dict(course_contract, schema_version=3, hops=3, progress_criterion='mapped_contact_v1')
    strict3 = dict(course_contract, schema_version=3, hops=3, progress_criterion='strict_travel_v1')
    if spec not in (expected, course_contract, mapped3, strict3):
        raise ValueError('Unsupported chain training contract')
    if config['task'] != 'a1_directed_jump_v5' or config['episode_seconds'] != 4.*spec['hops']:
        raise ValueError('Chain training requires directed jump and eight-second episodes')
    terrain = config.get('terrain_contract', {})
    allowed_terrain = ('deck', 'course') if spec in (course_contract,mapped3,strict3) else ('deck',)
    if terrain.get('mode') not in allowed_terrain or terrain.get('matched_material') is not True:
        raise ValueError('Chain training requires matched support allowed by its schema')
    jump = config['jump']
    if jump.get('train_forward_range_m') != [.15, .15] or jump.get('settle_seconds') != .3:
        raise ValueError('Chain training requires fixed 15cm goals and original preparation time')
    if any(key in jump for key in ('train_forward_choices_m', 'distance_curriculum', 'launch_curriculum')):
        raise ValueError('Chain training does not support goal or launch curricula')
    retention = config.get('retention_training')
    if spec in (course_contract,mapped3,strict3) and (retention is not None or config.get('support_assignment') is not None):
        raise ValueError('Version2 course comparison uses homogeneous two-hop training only')
    if retention is not None:
        retention = dict(retention)
        weights = retention.pop('single_goal_weights', None)
        if weights is not None and (weights != [1, 1, 1, 3] or
                any(type(x) is not int for x in weights) or
                retention.get('single_goal_choices_m') != [0., .05, .1, .15]):
            raise ValueError('Unsupported retention goal weights')
    if retention is not None and retention not in ({
            'schema_version': 1, 'single_fraction': .5, 'single_goal_choices_m': goals,
            'assignment': 'fixed_env_id_chain_first'} for goals in ([0., .15], [0., .05, .1, .15])):
        raise ValueError('Unsupported retention training contract')
    return dict(spec)


def assert_same_chain_training(old, new):
    validate_chain_training(old)
    validate_chain_training(new)
    if (old.get('chain_training') != new.get('chain_training') or
            old.get('retention_training') != new.get('retention_training')):
        raise ValueError('Checkpoint chain training contract differs; this is not a resume')
