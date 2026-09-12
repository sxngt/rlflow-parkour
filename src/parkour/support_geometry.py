"""Finite support surfaces in environment-local coordinates (metres).

This manifest describes geometry, not evidence of simulated contact. The caller
must create colliders and independently verify that gaps contain no support.
"""
from __future__ import annotations

import math


def build_support_layout(foot_names, foot_xy, *, mode, travel_m=0.15,
                         pad_length_m=0.09, pad_width_m=0.12,
                         thickness_m=0.10, catch_floor_z_m=-0.5, course_hops=2):
    if mode not in ('continuous', 'split', 'deck', 'course'):
        raise ValueError('Support mode must be continuous, split, deck or course')
    if type(course_hops) is not int or course_hops not in range(1,9):
        raise ValueError('Course supports one to eight hops')
    if mode == 'course':
        # Rear final pads approach front departure pads: 9 cm pads overlap.
        pad_length_m = .06
    dimensions = (travel_m, pad_length_m, pad_width_m, thickness_m)
    if any(not math.isfinite(v) or v <= 0 for v in dimensions):
        raise ValueError('Dimensions must be finite and positive')
    if not math.isfinite(catch_floor_z_m) or catch_floor_z_m >= -thickness_m:
        raise ValueError('Catch floor must lie below the support blocks')
    if len(foot_names) != 4 or len(set(foot_names)) != 4 or len(foot_xy) != 4:
        raise ValueError('Exactly four uniquely named feet are required')
    if any(len(p) != 2 or any(not math.isfinite(v) for v in p) for p in foot_xy):
        raise ValueError('Foot coordinates must be finite XY pairs')
    if mode == 'split' and travel_m <= pad_length_m:
        raise ValueError('Split supports require a positive gap')
    surfaces = []
    targets = []
    for name, (x, y) in zip(foot_names, foot_xy):
        targets.append({'foot': name, 'position_m': [x + travel_m, y, 0.]})
        segments = ([(x + travel_m / 2, pad_length_m + travel_m, 'bridge')]
                    if mode == 'continuous' else
                    [(x, pad_length_m, 'departure'),
                     (x + travel_m, pad_length_m, 'landing')])
        if mode == 'course':
            segments = [(x + k * travel_m, pad_length_m, f'station_{k}') for k in range(course_hops+1)]
        for cx, length, role in segments:
            surfaces.append({'id': f'{name}_{role}', 'foot': name, 'role': role,
                'center_m': [cx, y, -thickness_m / 2],
                'size_m': [length, pad_width_m, thickness_m],
                'normal': [0., 0., 1.], 'top_z_m': 0.,
                'bounds_xy_m': [cx-length/2, cx+length/2,
                                y-pad_width_m/2, y+pad_width_m/2]})
    if mode == 'deck':
        cx = sum(p[0] for p in foot_xy)/4 + travel_m/2
        cy = sum(p[1] for p in foot_xy)/4
        surfaces = [{'id': 'shared_deck', 'foot': 'all', 'role': 'shared',
                     'center_m': [cx, cy, -thickness_m/2],
                     'size_m': [1.4, 1.2, thickness_m], 'normal': [0., 0., 1.],
                     'top_z_m': 0., 'bounds_xy_m': [cx-.7, cx+.7, cy-.6, cy+.6]}]
    # Neighbouring feet must not accidentally bridge the intended holes.
    for i, a in enumerate(surfaces):
        for b in surfaces[i+1:]:
            ax0, ax1, ay0, ay1 = a['bounds_xy_m']
            bx0, bx1, by0, by1 = b['bounds_xy_m']
            if min(ax1, bx1) > max(ax0, bx0) and min(ay1, by1) > max(ay0, by0):
                raise ValueError(f"Overlapping supports: {a['id']}, {b['id']}")
    return {'schema_version': 1, 'frame': 'environment_local', 'mode': mode,
            'target_travel_m': travel_m,
            'gap_width_m': travel_m-pad_length_m if mode in ('split', 'course') else 0.,
            'catch_floor_z_m': catch_floor_z_m, 'surfaces': surfaces,
            'landing_targets': targets,
            'contact_margin_m': None,
            'contact_margin_note': 'Foot collision geometry must be measured before declaring usable contact area',
            'scope': 'Per-foot support transfer; not a whole-body gap-width claim'}


def support_ids_at_xy(layout, x, y):
    """Point coverage of top faces only; not a finite-radius contact query."""
    return [s['id'] for s in layout['surfaces']
            if s['bounds_xy_m'][0] <= x <= s['bounds_xy_m'][1]
            and s['bounds_xy_m'][2] <= y <= s['bounds_xy_m'][3]]


def expected_goal_surface(support, foot_index, nominal_xy, goal_forward_m, margin=.02):
    """Select the unique pad containing the commanded foot projection."""
    import math
    x,y=nominal_xy
    if not all(math.isfinite(v) for v in (x,y,goal_forward_m,margin)) or margin<0:
        raise ValueError('Invalid target geometry')
    surfaces=support['layout']['surfaces']
    candidates=surfaces if support['mode']=='deck' else [s for s in surfaces if s['foot']==support['foot_names'][foot_index]]
    matches=[]
    for s in candidates:
        x0,x1,y0,y1=s['bounds_xy_m']
        if x0+margin <= x+goal_forward_m <= x1-margin and y0+margin <= y <= y1-margin:
            matches.append(s)
    if len(matches)!=1:
        raise ValueError('Expected target must fit exactly one support surface')
    return matches[0]
