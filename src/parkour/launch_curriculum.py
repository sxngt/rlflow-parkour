"""Versioned update schedule; evaluation always uses the configured final radius."""
import math


def radius_for_update(config, update):
    if type(update) is not int or update < 0:
        raise ValueError('Update must be a nonnegative integer')
    jump = config.get('jump', {})
    schedule = jump.get('launch_curriculum')
    if schedule is None:
        return jump.get('launch_radius_m')
    if config.get('task') != 'a1_directed_jump_v5' or not schedule:
        raise ValueError('Launch curriculum requires a directed jump and nonempty stages')
    previous_step, previous_radius = -1, float('inf')
    radius = None
    for stage in schedule:
        step, value = stage['start_update'], stage['radius_m']
        if type(step) is not int or step <= previous_step or step < 0:
            raise ValueError('Stage updates must strictly increase from zero')
        if not math.isfinite(value) or value <= 0 or value > previous_radius:
            raise ValueError('Stage radii must be positive and nonincreasing')
        if step <= update:
            radius = value
        previous_step, previous_radius = step, value
    if schedule[0]['start_update'] != 0 or previous_radius != jump['launch_radius_m']:
        raise ValueError('Schedule must begin at zero and end at evaluation radius')
    return radius


def checkpoint_state(config, completed):
    if config.get('jump', {}).get('launch_curriculum') is None:
        return {'kind': 'fixed', 'target_offset_m': config['target_offset_m']}
    return {'kind': 'launch_radius_by_update_v1', 'completed_updates': completed,
            'next_rollout_radius_m': radius_for_update(config, completed),
            'transition_contract': 'reset_all_at_update_boundary; incomplete_episodes_discarded'}
