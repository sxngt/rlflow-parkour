"""Render oriented shared terrain and verify actual collider normals/positions."""
import argparse,json,math,sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,atomic_json,sha256
from parkour.shared_terrain import build_shared_course,build_long_shared_course
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--course',choices=['blocks','ramps','turns','mixed','long-easy','long-medium','long-hard'],default='mixed');args=p.parse_args()
config={'task':'shared_terrain_geometry_probe_v1','research_tags':['phase:P3','step:p3-17-shared-terrain','purpose:geometry-preview'],'course':args.course,'scope':'Terrain only; no robot policy or completed parkour claim'}
meta=begin_run(args.out,config,'probe')
try:
    launch_app(True)
    import torch
    import imageio.v2 as imageio
    import isaaclab.sim as sim_utils
    from isaaclab.sensors import Camera,CameraCfg
    from omni.physx import get_physx_scene_query_interface
    layout=build_long_shared_course(args.course.split('-')[1],1) if args.course.startswith('long-') else build_shared_course(args.course)
    sim=sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=.005,device='cuda:0',enable_scene_query_support=True))
    ground=sim_utils.GroundPlaneCfg();ground.func('/World/Ground',ground,translation=(0,0,layout['catch_floor_z_m']))
    light=sim_utils.DomeLightCfg(intensity=2500);light.func('/World/Light',light)
    for i,s in enumerate(layout['surfaces']):
        block=sim_utils.CuboidCfg(size=tuple(s['size_m']),collision_props=sim_utils.CollisionPropertiesCfg(),
            physics_material=sim_utils.RigidBodyMaterialCfg(static_friction=.5,dynamic_friction=.5,friction_combine_mode='average'),
            visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.25+.06*i,.4,.55)))
        block.func('/World/Surfaces/'+s['id'],block,translation=tuple(s['center_m']),orientation=tuple(s['orientation_wxyz']))
    camera=Camera(CameraCfg(prim_path='/World/Camera',height=720,width=1280,data_types=['rgb'],
        spawn=sim_utils.PinholeCameraCfg(focal_length=24.,horizontal_aperture=32.,clipping_range=(.1,100.))))
    sim.reset()
    query=get_physx_scene_query_interface();rays=[]
    for s in layout['surfaces']:
        origin=[a+.5*b for a,b in zip(s['top_center_m'],s['normal'])]
        hit=query.raycast_closest(tuple(origin),tuple(-x for x in s['normal']),1.)
        assert hit['hit'] and s['id'] in str(hit['collision']),hit
        error=math.sqrt(sum((a-float(b))**2 for a,b in zip(s['top_center_m'],hit['position'])))
        alignment=sum(a*float(b) for a,b in zip(s['normal'],hit['normal']))
        assert error<2e-5 and alignment>.9999,(s['id'],error,alignment)
        rays.append({'surface_id':s['id'],'hit_position_m':list(hit['position']),'hit_normal':list(hit['normal']),
                     'center_error_m':error,'normal_dot':alignment,'collider':str(hit['collision'])})
    centers=torch.tensor([s['top_center_m'] for s in layout['surfaces']],device='cuda:0')
    target=centers.mean(dim=0,keepdim=True)
    distance=max(5.5,float((centers.amax(dim=0)-centers.amin(dim=0)).norm())*1.3)
    def pose(index):
        angle=-.9+index/149*1.2
        eye=target+torch.tensor([[distance*math.cos(angle),distance*math.sin(angle),distance*.65]],device='cuda:0')
        camera.set_world_poses_from_view(eye,target)
    pose(0)
    for _ in range(30):sim.step();camera.update(.005)
    writer=imageio.get_writer(str(args.out/'terrain-preview.mp4'),fps=25,codec='libx264')
    for i in range(150):
        pose(i);sim.step();camera.update(.005)
        frame=camera.data.output['rgb'][0,:,:,:3].cpu().numpy()
        assert frame.max()>0
        if i==0:imageio.imwrite(args.out/'first-frame.png',frame)
        writer.append_data(frame)
    writer.close()
    atomic_json(args.out/'terrain.json',layout);atomic_json(args.out/'geometry-audit.json',{'rays':rays,'passed':True,'scope':'Center ray and normal checks; whole course feasibility not established'})
    atomic_json(args.out/'replay.json',{'artifact_type':'terrain_geometry_preview','policy_executed':False,'frames':150,'fps':25,'scope':config['scope']})
    meta['artifacts']={name:sha256(args.out/name) for name in ['terrain.json','geometry-audit.json','terrain-preview.mp4','first-frame.png','replay.json']}
    finish_run(args.out,meta)
except BaseException as error:traceback.print_exc();finish_run(args.out,meta,error)
