"""Training-only contact precision curriculum; fixed strict evaluation geometry."""
import math

def radius_for_update(config,update):
    if type(update) is not int or update<0:raise ValueError('Nonnegative update required')
    spec=config.get('contact_curriculum')
    if spec is None:return None
    if config.get('task')!='a1_continuous_tracker_v1' or spec.get('kind')!='contact_precision_v1':
        raise ValueError('Contact precision curriculum requires continuous Tracker')
    previous=-1;last=float('inf');active=None
    stages=spec['stages']
    for stage in stages:
        step,value=stage['start_update'],stage['radius_m']
        if type(step) is not int or step<=previous or step<0:raise ValueError('Increasing stages required')
        if not math.isfinite(value) or value<=0 or value>last:raise ValueError('Decreasing positive precision radii required')
        if step<=update:active=value
        previous,last=step,value
    if not stages or stages[0]['start_update']!=0 or last!=config['success_radius_m']:
        raise ValueError('Start at zero; end at strict evaluation radius')
    return active
