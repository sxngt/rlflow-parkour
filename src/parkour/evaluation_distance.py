"""Evaluation-only target override, with explicit finite-support containment."""
import copy
import math
from parkour.scenarios import directed_jump_scenarios


def distance_override(config, support, distances, episodes):
    if config['task']!='a1_directed_jump_v5' or not support or support['mode']!='continuous':
        raise ValueError('Distance override currently requires explicit continuous support')
    if not distances or len(set(distances))!=len(distances) or not all(math.isfinite(d) and d>=0 for d in distances):
        raise ValueError('Distances must be distinct finite nonnegative values')
    for name,(x,y) in zip(support['foot_names'],support['calibration']['foot_xy_m']):
        pad=next(s for s in support['layout']['surfaces'] if s['foot']==name)
        x0,x1,y0,y1=pad['bounds_xy_m']
        if not (y0+.02<=y<=y1-.02 and all(x0+.02<=x+d<=x1-.02 for d in distances)):
            raise ValueError('Evaluation target foot projection leaves support')
    jump=copy.deepcopy(config['jump']);jump['evaluation_forward_m']=list(distances)
    manifest=directed_jump_scenarios(episodes,jump)
    override={'from':config['jump']['evaluation_forward_m'],'to':list(distances),
              'scope':'evaluation scenarios only; checkpoint training config unchanged'}
    manifest['evaluation_distance_override']=copy.deepcopy(override)
    return manifest,override
