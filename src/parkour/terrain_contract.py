"""Versioned physical terrain contract shared by training and evaluation."""
import copy
import math
from parkour.support_geometry import build_support_layout
from parkour.jump_sampling import target_ranges


def training_support(config):
    spec = config.get('terrain_contract')
    if spec is None:
        return None
    if config['task']=='a1_continuous_tracker_v1':
        from parkour.shared_terrain import build_easy_shared_course,build_long_shared_course,scripted_pair_targets,assert_script_contacts_unoccluded
        if spec.get('schema_version')!=2 or spec.get('mode')!='shared-course' or spec.get('matched_material') is not True:
            raise ValueError('Continuous Tracker requires explicit shared-surface geometry')
        expected=(build_long_shared_course(spec['layout']['level'],spec['geometry_seed'],spec['layout'].get('transitions',10),spec['layout'].get('preparation_fraction',1.)) if spec['layout'].get('scenario_contract') in ('long_shared_course_v1','long_shared_course_v2','long_shared_blend_v1') else build_easy_shared_course(spec['geometry_seed']))
        if spec['layout'].get('scenario_contract') in ('long_ten_gap_course_v1','long_ten_gap_course_v2','long_ten_gap_course_v3'):
            from parkour.shared_terrain import build_ten_gap_course
            expected=build_ten_gap_course(spec['layout']['level'],spec['geometry_seed'],spec['layout']['gap_scale'],spec['layout'].get('approach_transfers',3),spec['layout'].get('gap_rise_m',0.))
        if spec['layout'].get('scenario_contract') in ('discrete_parkour_v1','discrete_parkour_v2','discrete_parkour_blend_v1'):
            from parkour.shared_terrain import build_discrete_parkour
            expected=build_discrete_parkour(spec['layout']['level'],spec['geometry_seed'],spec['layout']['transitions'],spec['layout'].get('preparation_fraction',1.))
        if spec['layout'].get('scenario_contract')=='mixed_discrete_v1':
            from parkour.shared_terrain import build_mixed_discrete
            expected=build_mixed_discrete(spec['geometry_seed'],spec['layout']['difficulty_fraction'])
        if spec['layout'].get('scenario_contract')=='mixed_discrete_axes_v1':
            from parkour.curriculum_maps import build_mixed_discrete_axes
            expected=build_mixed_discrete_axes(spec['geometry_seed'],spec['layout']['difficulty_axes'])
        if spec['layout']!=expected:
            raise ValueError('Shared training layout differs from generator')
        calibration=spec['calibration']
        if spec['foot_names']!=['FL_foot','FR_foot','RL_foot','RR_foot'] or len(calibration['root_state'])!=13 or len(calibration['joint_positions'])!=12:
            raise ValueError('Invalid shared terrain calibration')
        if not all(math.isfinite(v) for key in ('root_state','joint_positions') for v in calibration[key]):
            raise ValueError('Nonfinite calibration')
        script=scripted_pair_targets(spec['layout'],calibration['foot_xy_m'])
        assert_script_contacts_unoccluded(spec['layout'],script)
        return copy.deepcopy(spec)
    if config['task'] != 'a1_directed_jump_v5' or spec.get('schema_version') != 1:
        raise ValueError('Unsupported terrain training contract')
    if spec['mode'] not in ('flat', 'deck', 'continuous', 'split', 'course') or spec.get('matched_material') is not True:
        raise ValueError('Terrain training supports matched flat/deck/continuous/split/course only')
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
    generated = build_support_layout(spec['foot_names'], calibration['foot_xy_m'], mode=spec['mode'] if spec['mode'] != 'flat' else 'deck', course_hops=config.get('chain_training',{}).get('hops',2))
    if spec['mode'] != 'flat' and spec.get('layout') != generated:
        raise ValueError('Terrain layout differs from versioned generator')
    if spec['mode'] == 'flat' and 'layout' in spec:
        raise ValueError('Flat contract cannot contain finite geometry')
    if spec['mode'] in ('continuous', 'split', 'course'):
        margin = spec.get('foot_projection_radius_m')
        if margin != .02:
            raise ValueError('Finite foot supports require measured 2cm projection')
        jump = config['jump']
        ranges = [[0., 0.]] + target_ranges(jump)
        if spec['mode'] == 'course':
            ranges += [[.15*k,.15*k] for k in range(2,config.get('chain_training',{}).get('hops',2)+1)]
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
    validate_surface_materials(spec)
    return copy.deepcopy(spec)


def assert_same_terrain(old, new):
    if old.get('terrain_contract') != new.get('terrain_contract'):
        raise ValueError('Checkpoint terrain contract differs; this is not a resume')


def validate_surface_materials(spec):
    """Validate the explicit spatial friction contract before simulator startup."""
    variation=spec.get('friction_variation')
    overrides=spec.get('surface_material_overrides')
    if variation is None and overrides is None:
        return
    if spec.get('mode') != 'course' or not isinstance(variation,dict):
        raise ValueError('Material overrides require the spatial course contract')
    coefficient=variation.get('authored_friction');start=variation.get('start_station')
    if (not isinstance(coefficient,(int,float)) or not math.isfinite(coefficient) or not 0 <= coefficient <= .5
            or type(start) is not int or start<1 or variation.get('version')!='spatial_friction_v1'
            or variation.get('combine_mode')!='average'):
        raise ValueError('Invalid spatial friction contract')
    expected={surface['id']:{'static_friction':coefficient,'dynamic_friction':coefficient}
              for surface in spec['layout']['surfaces'] if int(surface['role'].split('_')[-1])>=start}
    if not expected or overrides!=expected:
        raise ValueError('Material overrides disagree with the declared station schedule')
