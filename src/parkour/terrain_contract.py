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
    if spec['mode'] not in ('flat', 'deck') or spec.get('matched_material') is not True:
        raise ValueError('Initial terrain training supports matched flat/deck only')
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
    generated = build_support_layout(spec['foot_names'], calibration['foot_xy_m'], mode='deck')
    if spec['mode'] == 'deck' and spec.get('layout') != generated:
        raise ValueError('Terrain layout differs from versioned generator')
    if spec['mode'] == 'flat' and 'layout' in spec:
        raise ValueError('Flat contract cannot contain finite geometry')
    return copy.deepcopy(spec)


def assert_same_terrain(old, new):
    if old.get('terrain_contract') != new.get('terrain_contract'):
        raise ValueError('Checkpoint terrain contract differs; this is not a resume')
