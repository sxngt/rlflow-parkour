"""Inspect every heterogeneous support collider before collecting training data."""
from pxr import Usd, UsdGeom, UsdPhysics, UsdShade
import numpy as np


def inspect_support_assignment(env):
    plan, stage = env.cfg.support_assignment, env.scene.stage
    assert plan and not env.cfg.scene.replicate_physics
    bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'proxy'], False)
    rows = []
    for group in plan['groups']:
        for index in range(group['env_start'], group['env_stop']):
            root = stage.GetPrimAtPath(f'/World/envs/env_{index}/Supports')
            assert root.IsValid(), index
            expected = {s['id'] for s in group['layout']['surfaces']}
            assert {p.GetName() for p in root.GetChildren()} == expected, (index, expected)
            origin = env.scene.env_origins[index].cpu().numpy()
            for surface in group['layout']['surfaces']:
                prim = stage.GetPrimAtPath(str(root.GetPath()) + '/' + surface['id'])
                colliders = [p for p in Usd.PrimRange(prim, Usd.TraverseInstanceProxies())
                             if p.HasAPI(UsdPhysics.CollisionAPI)]
                assert len(colliders) == 1, (index, surface['id'])
                collider = colliders[0]
                assert UsdPhysics.CollisionAPI(collider).GetCollisionEnabledAttr().Get()
                box = bbox.ComputeWorldBound(prim).ComputeAlignedRange()
                low, high = np.array(box.GetMin()) - origin, np.array(box.GetMax()) - origin
                center, size = np.array(surface['center_m']), np.array(surface['size_m'])
                assert np.allclose(low, center - size / 2, atol=1e-5, rtol=0), (index, low, center)
                assert np.allclose(high, center + size / 2, atol=1e-5, rtol=0), (index, high, center)
                material, _ = UsdShade.MaterialBindingAPI(collider).ComputeBoundMaterial('physics')
                assert material
                physics = UsdPhysics.MaterialAPI(material.GetPrim())
                assert physics.GetStaticFrictionAttr().Get() == .5
                assert physics.GetDynamicFrictionAttr().Get() == .5
                assert physics.GetRestitutionAttr().Get() == 0
                rows.append(dict(env_index=index, task=group['task'], mode=group['mode'],
                                 collider=str(collider.GetPath()), low_local_m=low.tolist(), high_local_m=high.tolist()))
    assert stage.GetPrimAtPath('/World/collisions').IsValid()
    return dict(schema_version=1, inspected_environments=env.num_envs, colliders=rows,
                scope='all USD support colliders, world bounds and material; collision group path exists; dynamic isolation requires separate probe')
