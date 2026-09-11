"""Physical drop probes for finite support geometry, without a learned policy."""
import argparse
import json
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from parkour.runtime import begin_run, finish_run, launch_app, atomic_json, sha256
from parkour.support_geometry import build_support_layout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--inspect-a1', action='store_true')
    parser.add_argument('--calibration-run', type=Path,
                        default=Path('artifacts/p2-11-curriculum-seed0__final-evaluation/run.json'))
    args = parser.parse_args()
    source = json.loads(args.calibration_run.read_text())
    config = {'task': 'finite_support_drop_probe_v1', 'physics_dt': .005,
              'research_tags': ['phase:P2', 'step:p2-14-support', 'purpose:implementation-check'],
              'calibration_source': str(args.calibration_run), 'probe_radius_m': .01,
              'inspect_a1': args.inspect_a1,
              'note': 'Sphere geometry probe; not robot transfer or foot collision validation'}
    meta = begin_run(args.out, config, 'probe')
    try:
        launch_app(False)
        import isaaclab.sim as sim_utils
        from isaaclab.assets import RigidObject, RigidObjectCfg
        from pxr import UsdPhysics, UsdGeom, Usd, PhysxSchema, Gf
        sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=.005, device='cuda:0'))
        if args.inspect_a1:
            from isaaclab_assets import UNITREE_A1_CFG
            asset = UNITREE_A1_CFG.spawn
            asset.func('/World/RobotInspector', asset, translation=(5., 0., .5))
            bbox = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render', 'proxy', 'guide'], False, True)
            feet = []
            for prim in Usd.PrimRange(sim.stage.GetPrimAtPath('/World/RobotInspector'), Usd.TraverseInstanceProxies()):
                if not prim.HasAPI(UsdPhysics.CollisionAPI):
                    continue
                bounds = bbox.ComputeLocalBound(prim).ComputeAlignedRange()
                collision = PhysxSchema.PhysxCollisionAPI(prim)
                world = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
                feet.append({'prim': str(prim.GetPath()), 'type': prim.GetTypeName(),
                    'radius': prim.GetAttribute('radius').Get(),
                    'local_bounds_min': None if bounds.IsEmpty() else list(bounds.GetMin()),
                    'local_bounds_max': None if bounds.IsEmpty() else list(bounds.GetMax()),
                    'world_axis_scale': [world.TransformDir(Gf.Vec3d(*axis)).GetLength()
                                         for axis in ((1,0,0), (0,1,0), (0,0,1))],
                    'local_transform': str(UsdGeom.Xformable(prim).GetLocalTransformation()),
                    'contact_offset': collision.GetContactOffsetAttr().Get(),
                    'rest_offset': collision.GetRestOffsetAttr().Get()})
            atomic_json(args.out/'a1-foot-colliders.json', {'usd_path': asset.usd_path,
                'colliders': feet, 'note': 'Local collider bounds; transforms must be included for physical foot extent'})
            assert feet, 'No collider found in A1 asset including instance proxies'
        ground = sim_utils.GroundPlaneCfg()
        ground.func('/World/CatchFloor', ground, translation=(0., 0., -.5))
        layouts, probes = [], []
        for mode, shift_y in [('continuous', -1.), ('split', 1.)]:
            layout = build_support_layout([f'foot_index_{i}' for i in range(4)],
                                          source['nominal_foot_xy_m'], mode=mode)
            layout['world_translation_m'] = [0., shift_y, 0.]
            layouts.append(layout)
            for surface in layout['surfaces']:
                block = sim_utils.CuboidCfg(size=tuple(surface['size_m']),
                    collision_props=sim_utils.CollisionPropertiesCfg(),
                    visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.3, .4, .5)))
                x, y, z = surface['center_m']
                block.func(f"/World/{mode}/{surface['id']}", block, translation=(x, y+shift_y, z))
            for index, (x, y) in enumerate(source['nominal_foot_xy_m']):
                for role, offset in [('departure', 0.), ('middle', .075), ('landing', .15)]:
                    name = f'{mode}_{index}_{role}'
                    sphere = RigidObject(RigidObjectCfg(prim_path=f'/World/Probes/{name}',
                        spawn=sim_utils.SphereCfg(radius=.01,
                            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
                            mass_props=sim_utils.MassPropertiesCfg(mass=.05),
                            collision_props=sim_utils.CollisionPropertiesCfg()),
                        init_state=RigidObjectCfg.InitialStateCfg(pos=(x+offset, y+shift_y, .2))))
                    expected = -.49 if mode == 'split' and role == 'middle' else .01
                    probes.append((name, sphere, expected))
        atomic_json(args.out/'terrain.json', layouts)
        sim.reset()
        traces = []
        for step in range(400):
            sim.step(render=False)
            for _, sphere, _ in probes:
                sphere.update(.005)
            if step % 10 == 0 or step == 399:
                traces.append({'time_s': (step+1)*.005,
                    'positions_m': {name: sphere.data.root_pos_w[0].tolist()
                                    for name, sphere, _ in probes}})
        results = []
        for name, sphere, expected in probes:
            xyz = sphere.data.root_pos_w[0].tolist()
            speed = float(sphere.data.root_lin_vel_w[0].norm())
            results.append({'probe': name, 'position_m': xyz, 'expected_center_z_m': expected,
                            'speed_m_s': speed, 'passed': abs(xyz[2]-expected) < .005 and speed < .02})
        colliders = [str(p.GetPath()) for p in sim.stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)]
        atomic_json(args.out/'probe.json', {'results': results, 'traces': traces,
            'collider_paths': colliders, 'passed': all(r['passed'] for r in results)})
        assert all(r['passed'] for r in results), results
        meta['artifacts'] = {p.name: sha256(p) for p in args.out.glob('*.json')
                             if p.name not in ('run.json', 'config.json')}
        finish_run(args.out, meta)
    except BaseException as error:
        traceback.print_exc()
        finish_run(args.out, meta, error)


if __name__ == '__main__':
    main()
