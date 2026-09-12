"""Evaluation-only target override, with explicit finite-support containment."""
import copy
import math
from parkour.scenarios import directed_jump_scenarios


def distance_override(config, support, distances, episodes):
    if config['task']!='a1_directed_jump_v5' or not support or support['mode'] not in ('continuous','split'):
        raise ValueError('Distance override currently requires explicit continuous or split support')
    if not distances or len(set(distances))!=len(distances) or not all(math.isfinite(d) and d>=0 for d in distances):
        raise ValueError('Distances must be distinct finite nonnegative values')
    from parkour.support_geometry import expected_goal_surface
    for i,xy in enumerate(support['calibration']['foot_xy_m']):
        for distance in distances:
            expected_goal_surface(support,i,xy,distance)
    jump=copy.deepcopy(config['jump']);jump['evaluation_forward_m']=list(distances)
    manifest=directed_jump_scenarios(episodes,jump)
    override={'from':config['jump']['evaluation_forward_m'],'to':list(distances),
              'scope':'evaluation scenarios only; checkpoint training config unchanged'}
    manifest['evaluation_distance_override']=copy.deepcopy(override)
    return manifest,override
