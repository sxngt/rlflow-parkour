"""Versioned physical terrain contract shared by training and evaluation."""
import copy
import math
from parkour.support_geometry import build_support_layout


def training_support(config):
    spec = config.get('terrain_contract')
    if spec is None:
        return None
    if config['task'] != 'a1_directed_jump_v5' or spec.get('schema_version') != 1:
        raise ValueError('Unsupported terrain training contract')
    if spec['mode'] not in ('flat', 'deck', 'continuous', 'split') or spec.get('matched_material') is not True:
        raise ValueError('Terrain training supports matched flat/deck/continuous/split only')
    if spec['foot_names'] != ['FL_foot', 'FR_foot', 'RL_foot', 'RR_foot']:
        raise ValueError('Unexpected calibrated foot order')
    calibration = spec['calibration']
    for key, size in [('root_state', 13), ('joint_positions', 12)]:
        if len(calibration[key]) != size or not all(math.isfinite(x) for x in calibration[key]):
            raise ValueError('Invalid calibration '+key)
    if not .2 < calibration['root_state'][2] < .4:
        raise ValueError('Invalid calibrated root height')
    if len(spec['reference_sha256']) != 64:
        raise ValueError('Missing reference hash')
    generated = build_support_layout(spec['foot_names'], calibration['foot_xy_m'], mode=spec['mode'] if spec['mode'] != 'flat' else 'deck')
    if spec['mode'] != 'flat' and spec.get('layout') != generated:
        raise ValueError('Terrain layout differs from versioned generator')
    if spec['mode'] == 'flat' and 'layout' in spec:
        raise ValueError('Flat contract cannot contain finite geometry')
    if spec['mode'] in ('continuous', 'split'):
        margin = spec.get('foot_projection_radius_m')
        if margin != .02:
            raise ValueError('Finite foot supports require measured 2cm projection')
        jump = config['jump']
        ranges = [[0., 0.], jump['train_forward_range_m']]
        ranges += [s['forward_range_m'] for s in jump.get('distance_curriculum', [])]
        ranges += [[d, d] for d in jump['evaluation_forward_m']]
        for limits in ranges:
            if len(limits) != 2 or not all(math.isfinite(d) for d in limits) or limits[0] > limits[1]:
                raise ValueError('Invalid support target range')
        for name, (x, y) in zip(spec['foot_names'], calibration['foot_xy_m']):
            surfaces = [s for s in generated['surfaces'] if s['foot'] == name]
            for low, high in ranges:
                # The WHOLE uniform interval must fit one convex support pad.
                # Endpoints on different pads must not conceal impossible gap targets.
                if not any(
                    s['bounds_xy_m'][0] + margin <= x + low and
                    x + high <= s['bounds_xy_m'][1] - margin and
                    s['bounds_xy_m'][2] + margin <= y <= s['bounds_xy_m'][3] - margin
                    for s in surfaces
                ):
                    raise ValueError('Target foot projection range leaves support')
    return copy.deepcopy(spec)


def assert_same_terrain(old, new):
    if old.get('terrain_contract') != new.get('terrain_contract'):
        raise ValueError('Checkpoint terrain contract differs; this is not a resume')
