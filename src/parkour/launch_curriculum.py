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
    if config.get('contact_curriculum') is not None:
        from parkour.contact_curriculum import radius_for_update as contact_radius
        return {'kind':'contact_precision_v1','completed_updates':completed,
                'next_contact_radius_m':contact_radius(config,completed),
                'transition_contract':'reset_all_at_update_boundary; incomplete_episodes_discarded'}
    if config.get('jump', {}).get('distance_curriculum') is not None:
        return {'kind': 'launch_and_distance_by_update_v1', 'completed_updates': completed,
                'next_rollout_radius_m': radius_for_update(config, completed),
                'next_rollout_forward_range_m': distance_for_update(config, completed),
                'transition_contract': 'reset_all_at_update_boundary; incomplete_episodes_discarded'}
    if config.get('jump', {}).get('launch_curriculum') is None:
        return {'kind': 'fixed', 'target_offset_m': config['target_offset_m']}
    return {'kind': 'launch_radius_by_update_v1', 'completed_updates': completed,
            'next_rollout_radius_m': radius_for_update(config, completed),
            'transition_contract': 'reset_all_at_update_boundary; incomplete_episodes_discarded'}


def distance_for_update(config, update):
    if type(update) is not int or update < 0:
        raise ValueError('Update must be a nonnegative integer')
    jump = config.get('jump', {})
    schedule = jump.get('distance_curriculum')
    if schedule is None:
        return jump.get('train_forward_range_m')
    if config.get('task') != 'a1_directed_jump_v5' or not schedule:
        raise ValueError('Distance curriculum requires directed jump and nonempty stages')
    previous_step, previous_high, active = -1, -1., None
    for stage in schedule:
        step, interval = stage['start_update'], stage['forward_range_m']
        if type(step) is not int or step < 0 or step <= previous_step:
            raise ValueError('Distance stage updates must strictly increase from zero')
        if len(interval) != 2 or not all(math.isfinite(v) for v in interval):
            raise ValueError('Distance range must contain two finite values')
        low, high = interval
        if low != 0 or high < 0 or high < previous_high:
            raise ValueError('Distance stages must expand a nonnegative range starting at zero')
        if step <= update:
            active = list(interval)
        previous_step, previous_high = step, high
    if schedule[0]['start_update'] != 0 or list(schedule[-1]['forward_range_m']) != jump['train_forward_range_m']:
        raise ValueError('Distance schedule must begin at zero and end at configured training range')
    return active
