"""Strict P2-34 chain training contract, distinct from runtime evaluation."""


def validate_chain_training(config):
    spec = config.get('chain_training')
    if spec is None:
        return None
    expected = {'schema_version': 1, 'hops': 2, 'forward_per_hop_m': .15,
                'hop_seconds': 4., 'settle_command': 'default'}
    if spec != expected:
        raise ValueError('Unsupported chain training contract')
    if config['task'] != 'a1_directed_jump_v5' or config['episode_seconds'] != 8.:
        raise ValueError('Chain training requires directed jump and eight-second episodes')
    terrain = config.get('terrain_contract', {})
    if terrain.get('mode') != 'deck' or terrain.get('matched_material') is not True:
        raise ValueError('Chain training requires matched deck support')
    jump = config['jump']
    if jump.get('train_forward_range_m') != [.15, .15] or jump.get('settle_seconds') != .3:
        raise ValueError('Chain training requires fixed 15cm goals and original preparation time')
    if any(key in jump for key in ('train_forward_choices_m', 'distance_curriculum', 'launch_curriculum')):
        raise ValueError('Chain training does not support goal or launch curricula')
    return dict(spec)


def assert_same_chain_training(old, new):
    validate_chain_training(old)
    validate_chain_training(new)
    if old.get('chain_training') != new.get('chain_training'):
        raise ValueError('Checkpoint chain training contract differs; this is not a resume')
