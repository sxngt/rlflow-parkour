"""Per-axis difficulty for the mixed discrete course (RLflow curriculum campaign, 2026-09-13).

`build_mixed_discrete(seed, f)` interpolates five geometry axes with one fraction and only accepts .25/.5/.75/1.
Every training arm at f>=.5 failed at the same transfer (surface 7→8, body collision), so the campaign needs
(1) arbitrary fractions and (2) independent fractions per axis to find and train the failing axis.
With all axes equal to f the output is identical to `build_mixed_discrete(seed, f)` (tests/test_curriculum_maps.py).

axes: gap (full-box clearance), turn (heading), tilt (roll/pitch), height (top z), size (landing footprint).
"""
from __future__ import annotations

import copy
import math

from parkour.shared_terrain import build_discrete_parkour, surface

AXES = ("gap", "turn", "tilt", "height", "size")
Z_TARGETS = [.12, .36, .48, .20, .28, .12, .42, .30, .12, .34, .20, .48, .30, .12, .38, .22, .40, .24, .12, .10, .0]
HEADINGS = [15, 0, 30, 0, 55, 55, 75, 75, 45, 15, 45, 15, 65, 65, 35, 0, 35, 0, 15, 0, 0]
CLEARANCES = [.28, .45, .30, .50, .40, .60, .35, .45, .30, .55, .35, .60, .40, .45, .30, .55, .35, .50, .40, .35, .25]
SIZES = [(.60, .50), (.80, .65), (.58, .52), (.90, .70), (.65, .55), (.60, .50), (.75, .60)]


def normalize_fractions(spec) -> dict[str, float]:
    """float → all axes; dict → missing axes default to 'base' (or .25)."""
    if isinstance(spec, (int, float)):
        f = float(spec)
        return {a: f for a in AXES}
    spec = dict(spec or {})
    base = float(spec.pop("base", .25))
    out = {a: float(spec.pop(a, base)) for a in AXES}
    if spec:
        raise ValueError(f"unknown difficulty axes {sorted(spec)}; use {AXES} or base")
    for a, v in out.items():
        if not (0. <= v <= 1.) or not math.isfinite(v):
            raise ValueError(f"fraction {a}={v} must be in [0, 1]")
    return out


def build_mixed_discrete_axes(seed: int = 1, fractions=None) -> dict:
    fr = normalize_fractions(fractions if fractions is not None else .25)
    base = build_discrete_parkour('medium', seed, 24, .75)
    surfaces = copy.deepcopy(base['surfaces'][:4])
    gaps = copy.deepcopy(base['gap_locations'][:3])
    for i in range(4, 25):
        old = base['surfaces'][i]
        R = old['rotation_local_to_world']
        j = i - 4
        old_angles = [math.degrees(math.atan2(R[2][1], R[2][2])), math.degrees(math.asin(-R[2][0])), math.degrees(math.atan2(R[1][0], R[0][0]))]
        desired = (0., 0., 0.) if i == 24 else ((-1 if i % 2 else 1) * (10 + i % 3 * 3), (-1 if i % 3 else 1) * (12 + i % 4 * 2), HEADINGS[j])
        f_rpy = (fr["tilt"], fr["tilt"], fr["turn"])
        rpy = [a + f * (b - a) for a, b, f in zip(old_angles, desired, f_rpy)]
        target_size = (1.2, 1.2) if i == 24 else SIZES[j % len(SIZES)]
        size = [old['size_m'][k] + fr["size"] * (target_size[k] - old['size_m'][k]) for k in (0, 1)] + [.18]
        z = old['top_center_m'][2] + fr["height"] * (Z_TARGETS[j] - old['top_center_m'][2])
        direction = [math.cos(math.radians(rpy[2])), math.sin(math.radians(rpy[2]))]
        candidate = surface('surface_' + str(i), [0., 0., z], size, rpy)

        def half(s, axes):
            return sum(abs(sum(direction[k] * s['rotation_local_to_world'][k][axis] for k in (0, 1))) * s['size_m'][axis] / 2 for axis in axes)

        clearance = base['gap_locations'][i - 1]['full_box_clearance_m'] + fr["gap"] * (CLEARANCES[j] - base['gap_locations'][i - 1]['full_box_clearance_m'])
        distance = half(surfaces[-1], range(3)) + half(candidate, range(3)) + clearance
        top_gap = distance - half(surfaces[-1], range(2)) - half(candidate, range(2))
        xy = [surfaces[-1]['top_center_m'][k] + distance * direction[k] for k in (0, 1)]
        candidate = surface('surface_' + str(i), [*xy, z], size, rpy)
        candidate['scenario_role'] = 'gap_landing'
        surfaces.append(candidate)
        gaps.append({'arrival_surface_index': i, 'projected_top_gap_m': top_gap, 'full_box_clearance_m': clearance, 'direction_xy': direction})
    f = next(iter(fr.values()))
    uniform = len({round(v, 9) for v in fr.values()}) == 1 and f in (.25, .5, .75, 1.)   # 원 generator 가 받는 값만 mixed_discrete_v1
    return {'schema_version': 2, 'geometry_contract': 'oriented_shared_surfaces_v1',
            'scenario_contract': 'mixed_discrete_v1' if uniform else 'mixed_discrete_axes_v1',
            'kind': 'mixed-discrete-challenge', 'level': 'development', 'seed': seed,
            'difficulty_fraction': f if uniform else None, 'difficulty_axes': dict(fr), 'transitions': 24, 'frame': 'course_local',
            'surfaces': surfaces, 'start_position_m': [0., 0., 0.], 'goal_position_m': surfaces[-1]['top_center_m'],
            'catch_floor_z_m': -.8, 'planned_gap_count': 24, 'gap_locations': gaps,
            'nominal_path_length_m': sum(math.dist(a['top_center_m'], b['top_center_m']) for a, b in zip(surfaces, surfaces[1:])),
            'scope': 'Mixed-width, sharp-turn, high/low and longer-gap development challenge; first three transfers retain stage2 approach. No policy feasibility certificate.'}


def describe(layout: dict, first: int = 0, last: int = 25) -> str:
    """Per-transfer table: heading change, tilt, rise, clearance, landing size."""
    lines = []
    S = layout['surfaces']
    for i in range(max(1, first), min(last, len(S))):
        a, b = S[i - 1], S[i]
        Rb = b['rotation_local_to_world']
        yaw = math.degrees(math.atan2(Rb[1][0], Rb[0][0]))
        Ra = a['rotation_local_to_world']
        yaw_a = math.degrees(math.atan2(Ra[1][0], Ra[0][0]))
        tilt = math.degrees(math.acos(max(-1., min(1., b['normal'][2]))))
        g = next((x for x in layout['gap_locations'] if x['arrival_surface_index'] == i), {})
        lines.append(f"{i:2d} turn={yaw - yaw_a:+6.1f}deg tilt={tilt:4.1f}deg rise={b['top_center_m'][2] - a['top_center_m'][2]:+.2f}m "
                     f"clear={g.get('full_box_clearance_m', 0):.2f}m top_gap={g.get('projected_top_gap_m', 0):.2f}m size={b['size_m'][0]:.2f}x{b['size_m'][1]:.2f}")
    return "\n".join(lines)
