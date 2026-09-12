"""Explicit history comparison on the existing oracle/contact-bit observation."""

def validate_history(config):
    spec=config.get('observation_history')
    if spec is None:return None
    base={'schema_version':1,'frames':8,'base_observation_dim':66,
          'normalization':'shared_current_frame','reset':'episode_boundary'}
    if config.get('task')!='a1_directed_jump_v5' or spec not in (
            dict(base,mode='stack'),dict(base,mode='zero_control')):
        raise ValueError('Unsupported observation history contract')
    return dict(spec)
