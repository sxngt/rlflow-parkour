"""Explicit command slew and motion-cost contract; no hardware feasibility claim."""
import math


def validate_motion(config):
    spec=config.get('motion_control')
    if spec is None:return None
    bounds={'target_speed_mps':(.2,4.),'speed_cost':(0.,20.),'joint_reference_rate_rad_s':(1.,30.),
            'joint_speed_soft_rad_s':(1.,30.),'joint_speed_cost':(0.,1.)}
    if not isinstance(spec,dict) or set(spec)!=set(bounds)|{'version'} or spec['version']!='motion_control_v1':
        raise ValueError('Invalid motion control contract')
    for key,(low,high) in bounds.items():
        value=spec[key]
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ValueError('Invalid motion parameter: '+key)
    return dict(spec)


def limit_reference(actions,previous,scale,dt,rate):
    """Limit normalized command increments, hence reference increments to rate*dt."""
    delta=rate*dt/scale
    return previous+(actions-previous).clamp(-delta,delta)
