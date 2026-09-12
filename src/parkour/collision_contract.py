"""Record resolved USD physics materials; do not invent unexposed solver defaults."""
from pxr import Usd, UsdPhysics, UsdShade, PhysxSchema, UsdGeom
import math


def recorded_value(value):
    return {'nonfinite_usd_value': str(value)} if isinstance(value, float) and not math.isfinite(value) else value


def inspect_collision_contract(env):
    stage = env.scene.stage
    roots = ['/World/Ground', '/World/envs/env_0']
    if env.num_envs > 1:
        roots.append(f'/World/envs/env_{env.num_envs-1}')
    rows = []
    for root in roots:
        for prim in Usd.PrimRange(stage.GetPrimAtPath(root), Usd.TraverseInstanceProxies()):
            if not prim.HasAPI(UsdPhysics.CollisionAPI):
                continue
            material, relationship = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial('physics')
            values = None
            if material:
                physics = UsdPhysics.MaterialAPI(material.GetPrim())
                physx = PhysxSchema.PhysxMaterialAPI(material.GetPrim())
                values = {'path': str(material.GetPath()),
                          'static_friction': physics.GetStaticFrictionAttr().Get(),
                          'dynamic_friction': physics.GetDynamicFrictionAttr().Get(),
                          'restitution': physics.GetRestitutionAttr().Get(),
                          'friction_combine_mode': physx.GetFrictionCombineModeAttr().Get(),
                          'restitution_combine_mode': physx.GetRestitutionCombineModeAttr().Get()}
            collision = PhysxSchema.PhysxCollisionAPI(prim)
            rows.append({'prim': str(prim.GetPath()), 'shape': prim.GetTypeName(),
                         'physics_material': values,
                         'binding_relationship': str(relationship.GetPath()) if relationship else None,
                         'contact_offset': recorded_value(collision.GetContactOffsetAttr().Get()),
                         'rest_offset': recorded_value(collision.GetRestOffsetAttr().Get())})
    assert rows, 'No collision shapes inspected'
    if env.cfg.support_contract.get('matched_material'):
        surfaces = [r for r in rows if '/Supports/' in r['prim'] or '/World/Ground/' in r['prim']]
        assert surfaces, 'No support material inspected'
        for row in surfaces:
            material = row['physics_material']
            expected = {'static_friction':.5, 'dynamic_friction':.5}
            for surface_id, override in env.cfg.support_contract.get('surface_material_overrides', {}).items():
                if '/Supports/'+surface_id+'/' in row['prim'] or row['prim'].endswith('/Supports/'+surface_id):
                    expected = override
                    break
            assert material and all(abs(material[k]-v)<1e-7 for k,v in expected.items()), row
            assert material['restitution'] == 0 and material['friction_combine_mode'] == 'average', row
    elevated_bounds=[]
    if (env.cfg.support_contract.get('layout',{}).get('height_contract') or env.cfg.support_contract.get('layout',{}).get('geometry_contract')=='full_platform_gap_v1'):
        cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        surfaces={s['id']:s for s in env.cfg.support_contract['layout']['surfaces']}
        for row in rows:
            if '/Supports/' not in row['prim']:continue
            name=row['prim'].split('/Supports/')[1].split('/')[0]
            if name not in surfaces:continue
            index=int(row['prim'].split('/envs/env_')[1].split('/')[0])
            origin=env.scene.env_origins[index].detach().cpu().tolist()
            bound=cache.ComputeWorldBound(stage.GetPrimAtPath(row['prim'])).ComputeAlignedRange()
            low=[float(x)-o for x,o in zip(bound.GetMin(),origin)]
            high=[float(x)-o for x,o in zip(bound.GetMax(),origin)]
            surface=surfaces[name]
            expected_low=[c-size/2 for c,size in zip(surface['center_m'],surface['size_m'])]
            expected_high=[c+size/2 for c,size in zip(surface['center_m'],surface['size_m'])]
            assert all(abs(a-b)<2e-5 for a,b in zip(low+high,expected_low+expected_high)), (row['prim'],low,high)
            elevated_bounds.append({'prim':row['prim'],'bounds_min_local_m':low,'bounds_max_local_m':high})
        assert len(elevated_bounds)==len(surfaces)*(2 if env.num_envs>1 else 1)
    gap_queries=[]
    if env.cfg.support_contract.get('mode')=='full-gap':
        from omni.physx import get_physx_scene_query_interface
        query=get_physx_scene_query_interface()
        layout=env.cfg.support_contract['layout'];departure,landing=layout['surfaces']
        for index in sorted({0,env.num_envs-1}):
            origin=env.scene.env_origins[index].detach().cpu().tolist()
            y=departure['center_m'][1]+.45
            for name,x,z in [('departure',departure['center_m'][0],0.),
                             ('gap',(departure['bounds_xy_m'][1]+landing['bounds_xy_m'][0])/2,layout['catch_floor_z_m']),
                             ('landing',landing['center_m'][0],0.)]:
                result=query.raycast_closest((x+origin[0],y+origin[1],origin[2]+.5),(0.,0.,-1.),2.)
                assert result['hit'], (name,result)
                actual=float(result['position'][2])-origin[2]
                assert abs(actual-z)<2e-5, (name,actual,z)
                gap_queries.append({'env_index':index,'probe':name,'hit_z_local_m':actual,
                                    'expected_z_local_m':z,'collider':str(result.get('collision',''))})
    return {'schema_version': 1, 'roots': roots, 'colliders': rows, 'elevated_support_bounds':elevated_bounds, 'full_gap_ray_queries':gap_queries,
            'scope': 'Resolved USD binding in first/last environment and global ground. Null means unspecified; not a measured solver default.',
            'matched_support_material': bool(env.cfg.support_contract.get('matched_material')) and all(
                v==.5 for override in env.cfg.support_contract.get('surface_material_overrides',{}).values() for v in override.values()),
            'base_material_matched': bool(env.cfg.support_contract.get('matched_material')),
            'surface_material_override_count':len(env.cfg.support_contract.get('surface_material_overrides',{}))}
