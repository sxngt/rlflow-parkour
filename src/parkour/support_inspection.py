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


def inspect_terrain_mix(env):
    """terrain_mix 그룹별 스폰 검사: 회전된 cuboid 는 월드 AABB 가 8개 꼭짓점의 min/max 와 같아야 한다 (축 정렬 가정 없음)."""
    import itertools
    plan, stage = env.cfg.support_assignment, env.scene.stage
    assert plan and plan.get('kind') == 'terrain_mix' and not env.cfg.scene.replicate_physics
    bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'proxy'], False)
    rows = []
    for gi, group in enumerate(plan['groups']):
        # 그룹의 첫·마지막 env 만 정밀 검사 (같은 layout 의 복제), 모든 env 는 prim 존재만 확인
        for index in range(group['env_start'], group['env_stop']):
            root = stage.GetPrimAtPath(f'/World/envs/env_{index}/Supports')
            assert root.IsValid(), index
            if index not in (group['env_start'], group['env_stop'] - 1):
                continue
            expected = {s['id'] for s in group['layout']['surfaces']}
            assert {p.GetName() for p in root.GetChildren()} == expected, (index, expected)
            origin = env.scene.env_origins[index].cpu().numpy()
            for surface in group['layout']['surfaces']:
                prim = stage.GetPrimAtPath(str(root.GetPath()) + '/' + surface['id'])
                colliders = [p for p in Usd.PrimRange(prim, Usd.TraverseInstanceProxies()) if p.HasAPI(UsdPhysics.CollisionAPI)]
                assert len(colliders) == 1 and UsdPhysics.CollisionAPI(colliders[0]).GetCollisionEnabledAttr().Get(), (index, surface['id'])
                box = bbox.ComputeWorldBound(prim).ComputeAlignedRange()
                low, high = np.array(box.GetMin()) - origin, np.array(box.GetMax()) - origin
                R = np.array(surface['rotation_local_to_world']); c = np.array(surface['center_m']); h = np.array(surface['size_m']) / 2
                corners = np.array([c + R @ (np.array(sgn) * h) for sgn in itertools.product((-1, 1), repeat=3)])
                assert np.allclose(low, corners.min(axis=0), atol=2e-3, rtol=0), (gi, index, surface['id'], low, corners.min(axis=0))
                assert np.allclose(high, corners.max(axis=0), atol=2e-3, rtol=0), (gi, index, surface['id'], high, corners.max(axis=0))
                rows.append({'group': gi, 'env': index, 'surface': surface['id'], 'aabb_low_m': low.tolist(), 'aabb_high_m': high.tolist()})
    return {'contract': 'terrain_mix_oriented_cuboid_aabb_v1', 'groups': len(plan['groups']), 'checked_prims': len(rows), 'rows': rows}
