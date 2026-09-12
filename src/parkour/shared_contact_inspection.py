"""Ray-audit planned contact points against actual cloned terrain colliders."""
import math

def inspect_shared_contacts(env):
    from omni.physx import get_physx_scene_query_interface
    query=get_physx_scene_query_interface();rows=[]
    for env_id in sorted({0,env.num_envs-1}):
        offset=env.scene.env_origins[env_id].detach().cpu().tolist()
        for group,targets in enumerate(env.target_script['positions_m']):
            for index,pair in enumerate(targets):
                if index==0:continue  # Robot itself can occlude initial foot rays.
                surface=env.layout['surfaces'][index];normal=surface['normal']
                for foot,point in enumerate(pair):
                    origin=[a+o+.1*n for a,o,n in zip(point,offset,normal)]
                    hit=query.raycast_closest(tuple(origin),tuple(-n for n in normal),.5)
                    expected=[a+o-.02*n for a,o,n in zip(point,offset,normal)]
                    assert hit['hit'],(env_id,index,foot)
                    collider=str(hit['collision'])
                    assert f'/env_{env_id}/Supports/{surface["id"]}/' in collider,collider
                    error=math.sqrt(sum((float(a)-b)**2 for a,b in zip(hit['position'],expected)))
                    alignment=sum(float(a)*b for a,b in zip(hit['normal'],normal))
                    assert error<5e-5 and alignment>.9999,(collider,error,alignment)
                    rows.append({'env':env_id,'group':group,'target_index':index,'foot_in_pair':foot,
                        'collider':collider,'point_error_m':error,'normal_dot':alignment})
    return {'passed':True,'rays':rows,'scope':'Noninitial scripted foot targets in first/last clones; initial robot contacts checked separately'}
