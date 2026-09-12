"""Offline event reconstruction from recorded world-frame physics samples."""
import numpy as np

def reconstruct_flights(force, root_z, root_vz, nonfoot_force, dt):
    supported=(np.linalg.norm(force,axis=-1)>2).any(axis=-1)
    events=[];start=None;had_support=False
    for index,support in enumerate(supported):
        if not support and start is None and had_support:
            start=index
        if support and start is not None:
            window=slice(start,index+1)
            duration=(index-start)*dt
            rise=float(root_z[window].max()-root_z[max(0,start-1)])
            upward=bool((root_vz[window]>.2).any())
            collision=bool((nonfoot_force[window]>5).any())
            events.append({'takeoff_sample':start,'landing_sample':index,
                'air_seconds':duration,'root_rise_m':rise,'upward_velocity':upward,
                'nonfoot_collision':collision,
                'counted_jump':bool(duration>=.02-1e-7 and rise>=.03 and upward and not collision)})
            start=None
        had_support=had_support or bool(support)
    return events
