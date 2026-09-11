"""Record resolved USD physics materials; do not invent unexposed solver defaults."""
from pxr import Usd, UsdPhysics, UsdShade, PhysxSchema
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
    if env.cfg.evaluation_support.get('matched_material'):
        surfaces = [r for r in rows if '/Supports/' in r['prim'] or '/World/Ground/' in r['prim']]
        assert surfaces, 'No support material inspected'
        for row in surfaces:
            material = row['physics_material']
            assert material and material['static_friction'] == .5 and material['dynamic_friction'] == .5, row
            assert material['restitution'] == 0 and material['friction_combine_mode'] == 'average', row
    return {'schema_version': 1, 'roots': roots, 'colliders': rows,
            'scope': 'Resolved USD binding in first/last environment and global ground. Null means unspecified; not a measured solver default.',
            'matched_support_material': bool(env.cfg.evaluation_support.get('matched_material'))}
