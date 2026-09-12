"""Held-out shared-course geometry; leaves checkpoint's training config intact."""
import copy
from parkour.shared_terrain import build_long_shared_course,scripted_pair_targets,assert_script_contacts_unoccluded

def override_course(support,level,seed):
    if support.get('mode')!='shared-course' or type(seed) is not int or seed<0:
        raise ValueError('Shared course and nonnegative geometry seed required')
    changed=copy.deepcopy(support)
    changed['layout']=build_long_shared_course(level,seed)
    changed['geometry_seed']=seed
    script=scripted_pair_targets(changed['layout'],changed['calibration']['foot_xy_m'])
    assert_script_contacts_unoccluded(changed['layout'],script)
    return changed
