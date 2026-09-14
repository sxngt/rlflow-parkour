"""Ray-audit planned contact points against actual cloned terrain colliders."""
import math

def position_tolerance(origin,expected):
    """Base ray tolerance plus two float32 ULPs per world-coordinate axis."""
    ulps=[]
    for a,b in zip(origin,expected):
        scale=max(abs(a),abs(b))
        if not math.isfinite(scale):raise ValueError('Nonfinite ray coordinates')
        ulps.append(2.**(math.frexp(scale)[1]-24) if scale else 2.**-149)
    tolerance=5e-5+2*math.sqrt(sum(u*u for u in ulps))
    if tolerance>1e-3:raise ValueError('World-coordinate precision exceeds 1mm audit budget')
    return tolerance

def inspect_shared_contacts(env):
    from omni.physx import get_physx_scene_query_interface
    query=get_physx_scene_query_interface();rows=[]
    # terrain_mix: 그룹마다 layout 이 다르므로 그룹의 첫·마지막 env 를 그 그룹의 layout/스크립트로 검사한다
    checks=[]
    mix=getattr(env,'mix',None)
    if mix:
        from parkour.shared_terrain import scripted_pair_targets
        for g in mix['groups']:
            script=scripted_pair_targets(g['layout'],env.calibration['foot_xy_m'],initial_rear_target=env.cfg.initial_rear_target)
            for env_id in sorted({g['env_start'],g['env_stop']-1}):
                checks.append((env_id,g['layout'],script))
    else:
        checks=[(env_id,env.layout,env.target_script) for env_id in sorted({0,env.num_envs-1})]
    for env_id,layout,script in checks:
        offset=env.scene.env_origins[env_id].detach().cpu().tolist()
        for group,targets in enumerate(script['positions_m']):
            for index,pair in enumerate(targets):
                if index==0:continue  # Robot itself can occlude initial foot rays.
                surface=layout['surfaces'][index];normal=surface['normal']
                for foot,point in enumerate(pair):
                    origin=[a+o+.1*n for a,o,n in zip(point,offset,normal)]
                    hit=query.raycast_closest(tuple(origin),tuple(-n for n in normal),.5)
                    expected=[a+o-.02*n for a,o,n in zip(point,offset,normal)]
                    assert hit['hit'],(env_id,index,foot)
                    collider=str(hit['collision'])
                    assert f'/env_{env_id}/Supports/{surface["id"]}/' in collider,collider
                    error=math.sqrt(sum((float(a)-b)**2 for a,b in zip(hit['position'],expected)))
                    alignment=sum(float(a)*b for a,b in zip(hit['normal'],normal))
                    tolerance=position_tolerance(origin,expected)
                    assert error<tolerance and alignment>.9999,(collider,error,alignment,tolerance)
                    rows.append({'env':env_id,'group':group,'target_index':index,'foot_in_pair':foot,
                        'collider':collider,'point_error_m':error,'position_tolerance_m':tolerance,'normal_dot':alignment})
    return {'passed':True,'rays':rows,'scope':'Noninitial scripted foot targets in first/last clones; initial robot contacts checked separately'}
