"""Held-out shared-course geometry; leaves checkpoint's training config intact."""
import copy
from parkour.shared_terrain import build_long_shared_course,scripted_pair_targets,assert_script_contacts_unoccluded

def override_course(support,level,seed,transitions=None):
    if support.get('mode')!='shared-course' or type(seed) is not int or seed<0:
        raise ValueError('Shared course and nonnegative geometry seed required')
    changed=copy.deepcopy(support)
    if support['layout'].get('scenario_contract') in ('long_ten_gap_course_v1','long_ten_gap_course_v2'):
        from parkour.shared_terrain import build_ten_gap_course
        if transitions not in (None,40,60):raise ValueError('Ten-gap route requires forty or sixty foot transfers')
        approaches=transitions//10-1 if transitions else support['layout'].get('approach_transfers',3)
        changed['layout']=build_ten_gap_course(level,seed,support['layout']['gap_scale'],approaches)
    else:changed['layout']=build_long_shared_course(level,seed,transitions or 10)
    changed['geometry_seed']=seed
    script=scripted_pair_targets(changed['layout'],changed['calibration']['foot_xy_m'])
    assert_script_contacts_unoccluded(changed['layout'],script)
    return changed
