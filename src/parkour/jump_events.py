"""Sampled flight/landing gates, independent of simulator side effects."""
import math
import torch

def jump_transition(seen,landed,touched,contact,air_window,settled,rise,vz,errors,apex,required_apex,
                    angular_speed,height_error,history_supported,failure,hold,dt,spec):
    flight_event=(~seen)&air_window&settled&(rise>=spec['flight_min_rise_m'])&(vz>=spec['flight_min_vz_m_s'])&~failure
    new_seen=seen|flight_event
    new_touch=(seen[:,None]&contact)&~touched
    new_touched=touched|new_touch
    new_landed=landed|new_touch.any(dim=1)
    stable=(new_seen&new_landed&history_supported&contact.all(dim=1)&(errors<=spec['landing_radius_m']).all(dim=1)
            &(apex>=required_apex)&(vz.abs()<=spec['final_vz_max_m_s'])
            &(angular_speed<=spec['final_angular_speed_max_rad_s'])&(height_error.abs()<=spec['final_height_error_max_m'])&~failure)
    new_hold=torch.where(stable,hold+1,0)
    success=(new_hold>=math.ceil(spec['final_hold_seconds']/dt))&~failure
    return new_seen,new_landed,new_touched,new_hold,flight_event,new_touch,success


def apex_progress(apex,required_apex,min_rise,previous):
    """Bounded once-per-episode progress above the flight-detection floor."""
    progress=((apex-min_rise)/(required_apex-min_rise).clamp_min(1e-6)).clamp(0,1)
    progress=torch.maximum(progress,previous)
    return progress,progress-previous


def landing_height_cost(rise,landed,tolerance):
    return (rise/tolerance).square().clamp_max(4)*landed


def landing_settle_cost(vz,contact,landed,velocity_weight,support_weight):
    return landed*(velocity_weight*vz.square()+support_weight*(1-contact.float().mean(dim=1)))
