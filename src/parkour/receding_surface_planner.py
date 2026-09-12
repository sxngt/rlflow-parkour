"""Four-contact geometric beam search. No Tracker rollout feasibility claim."""
import math
import time


def plan_surfaces(layout,current_surface_id,root_xy,velocity_xy,*,horizon=4,beam_width=12,max_distance=1.8,max_height=.4,budget_ms=20.,blocked=()):
    start=time.perf_counter()
    if horizon not in (3,4) or beam_width<1 or budget_ms<=0:raise ValueError('Invalid planning budget')
    surfaces={s['id']:s for s in layout['surfaces']}
    if len(surfaces)!=len(layout['surfaces']) or current_surface_id not in surfaces:raise ValueError('Invalid surface IDs')
    goal=layout['goal_position_m'];blocked=set(blocked)
    def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
    source=surfaces[current_surface_id]
    # Path, accumulated transition cost, last direction. Fresh observed state each call.
    speed=math.hypot(*velocity_xy)
    direction=[v/speed for v in velocity_xy] if speed>.15 else [0.,0.]
    beam=[([current_surface_id],0.,direction)];best=None;expanded=0;timeout=False
    for depth in range(horizon):
        candidates=[]
        for path,cost,previous in beam:
            a=surfaces[path[-1]]['top_center_m']
            for sid,s in sorted(surfaces.items()):
                if (time.perf_counter()-start)*1000>budget_ms:timeout=True;break
                b=s['top_center_m'];length=dist(a,b)
                if sid in blocked or sid in path or not .1<length<=max_distance:continue
                if abs(b[2]-a[2])>max_height or s['normal'][2]<math.cos(math.radians(25)):continue
                if min(s['usable_half_extents_m'])<.2 or dist(b,goal)>=dist(a,goal)-.01:continue
                heading=[(b[k]-a[k])/length for k in (0,1)]
                turn=1-sum(x*y for x,y in zip(previous,heading))
                # State-conditioned first approach, geometry-only continuation.
                approach=dist(root_xy,b) if depth==0 else length
                score=cost+.2*length+2*abs(b[2]-a[2])+ .4*turn +(.05*approach if depth==0 else 0.)
                candidates.append((path+[sid],score,heading));expanded+=1
            if timeout:break
        if not candidates:break
        candidates.sort(key=lambda item:(item[1]+dist(surfaces[item[0][-1]]['top_center_m'],goal),item[0]))
        beam=candidates[:beam_width];best=beam[0]
        if dist(surfaces[best[0][-1]]['top_center_m'],goal)<1e-6 or timeout:break
    ids=[] if best is None else best[0][1:]
    complete=len(ids)==horizon or (ids and dist(surfaces[ids[-1]]['top_center_m'],goal)<1e-6)
    return {'planner':'receding_surface_beam_v1','status':'timeout' if timeout else ('planned' if complete else 'no_plan'),
        'horizon':horizon,'surface_ids':ids,'contacts':[{'surface_id':sid,'center_m':surfaces[sid]['top_center_m'],'normal':surfaces[sid]['normal']} for sid in ids],
        'expanded':expanded,'elapsed_ms':(time.perf_counter()-start)*1000,
        'scope':'Geometric shadow planner, observed state input; not connected to actuator targets and no physical Tracker rollout validation'}
