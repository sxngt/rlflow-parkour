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
    if spec['mode'] not in ('flat', 'deck', 'continuous') or spec.get('matched_material') is not True:
        raise ValueError('Terrain training supports matched flat/deck/continuous only')
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
    if spec['mode'] == 'continuous':
        # Fixed per-foot rectangles: endpoint containment proves every interpolated
        # forward target fits. This is geometry, not dynamic reachability.
        margin = spec.get('foot_projection_radius_m')
        if margin != .02:
            raise ValueError('Continuous support requires measured 2cm foot projection')
        jump = config['jump']
        distances = [0.0] + list(jump['train_forward_range_m']) + list(jump['evaluation_forward_m'])
        for stage in jump.get('distance_curriculum', []):
            distances.extend(stage['forward_range_m'])
        if not distances or not all(math.isfinite(d) for d in distances):
            raise ValueError('Invalid support target distance')
        for name, (x, y) in zip(spec['foot_names'], calibration['foot_xy_m']):
            surface = next(s for s in generated['surfaces'] if s['foot'] == name)
            x0, x1, y0, y1 = surface['bounds_xy_m']
            if not (y0 + margin <= y <= y1 - margin and
                    all(x0 + margin <= x + d <= x1 - margin for d in distances)):
                raise ValueError('Target foot projection leaves continuous support')
    return copy.deepcopy(spec)


def assert_same_terrain(old, new):
    if old.get('terrain_contract') != new.get('terrain_contract'):
        raise ValueError('Checkpoint terrain contract differs; this is not a resume')
