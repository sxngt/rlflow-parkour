"""Finite horizontal-map planner for translation-only four-foot stances.

This baseline checks geometry, not dynamics. It does not use surface foot/role
labels or precomputed landing targets. Tracker capability is checked separately.
"""
from collections import deque
import math
import time


def plan_stances(layout, nominal_xy, goal_forward_m, *, margin_m=.02,
                 min_step_m=.04, max_step_m=.16, max_hops=2, max_step_height_m=None):
    started = time.perf_counter()
    if len(nominal_xy) != 4 or any(len(p) != 2 for p in nominal_xy):
        raise ValueError('Four nominal XY foot coordinates required')
    numbers = [v for p in nominal_xy for v in p] + [goal_forward_m, margin_m, min_step_m, max_step_m]
    if not all(math.isfinite(v) for v in numbers) or not 0 <= margin_m or not 0 < min_step_m <= max_step_m or goal_forward_m <= 0 or max_hops < 1:
        raise ValueError('Invalid geometric planning contract')
    if max_step_height_m is not None and (not math.isfinite(max_step_height_m) or not 0 < max_step_height_m <= .05):
        raise ValueError('Invalid vertical step limit')
    surfaces = sorted(layout['surfaces'], key=lambda s: s['id'])
    if len(surfaces) > 256 or len({s['id'] for s in surfaces}) != len(surfaces):
        raise ValueError('Map exceeds baseline candidate budget or contains duplicate IDs')
    candidates, rejected = [], []
    offsets = sorted({0., *[round(s['center_m'][0] - nominal_xy[0][0], 8) for s in surfaces]})
    for dx in offsets:
        if dx < -1e-7 or dx > goal_forward_m + 1e-7:
            continue
        ids = []
        for x, y in nominal_xy:
            matches = []
            for s in surfaces:
                a,b,c,d = s['bounds_xy_m']
                if ((max_step_height_m is not None or abs(s['top_z_m']) < 1e-8) and s['normal'] == [0.,0.,1.]
                    and a+margin_m-1e-7 <= x+dx <= b-margin_m+1e-7
                    and c+margin_m-1e-7 <= y <= d-margin_m+1e-7):
                    matches.append(s['id'])
            if len(matches) != 1:
                break
            ids.append(matches[0])
        if len(ids) != 4 or len(set(ids)) != 4:
            rejected.append({'forward_m':dx,'reason':'four distinct unambiguous margin-safe surfaces unavailable'})
        else:
            candidate = {'forward_m':dx,'surface_ids':ids,
                         'foot_xy_m':[[x+dx,y] for x,y in nominal_xy]}
            if max_step_height_m is not None:
                heights = [next(s['top_z_m'] for s in surfaces if s['id']==sid) for sid in ids]
                if any(not math.isfinite(z) for z in heights) or max(heights)-min(heights)>1e-7:
                    rejected.append({'forward_m':dx,'reason':'stance requires four equal-height horizontal surfaces'})
                    continue
                candidate['support_height_m'] = heights[0]
                candidate['foot_xyz_m'] = [[x+dx,y,z] for (x,y),z in zip(nominal_xy,heights)]
            candidates.append(candidate)
    start = next((i for i,c in enumerate(candidates) if abs(c['forward_m']) < 1e-7), None)
    queue = deque([(start, [])]) if start is not None else deque()
    visited = {start}
    selected = None
    while queue:
        node, path = queue.popleft()
        if abs(candidates[node]['forward_m']-goal_forward_m) < 1e-7:
            selected = path
            break
        if len(path) >= max_hops:
            continue
        for nxt,c in enumerate(candidates):
            delta = c['forward_m']-candidates[node]['forward_m']
            height_ok = max_step_height_m is None or abs(c['support_height_m']-candidates[node]['support_height_m']) <= max_step_height_m+1e-7
            if height_ok and min_step_m-1e-7 <= delta <= max_step_m+1e-7 and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt,path+[nxt]))
    result = {'schema_version':1,'planner':'horizontal_translation_graph_v1',
            'status':'planned' if selected is not None else 'no_plan',
            'goal_forward_m':goal_forward_m,'margin_m':margin_m,
            'min_step_m':min_step_m,'max_step_m':max_step_m,'max_hops':max_hops,
            'candidates':candidates,'rejected':rejected,
            'contacts':[] if selected is None else [candidates[i] for i in selected],
            'elapsed_ms':(time.perf_counter()-started)*1000,
            'scope':'geometric horizontal translation only; no dynamics, body swept-volume or rollout validation'}

    if max_step_height_m is not None:
        result.update(planner='level_stance_height_graph_v1', max_step_height_m=max_step_height_m,
                      scope='geometric equal-height stance translations; no slopes, dynamics or swept-volume validation')
    return result
