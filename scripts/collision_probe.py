"""Controlled collision instrumentation probes; no learned policy performance claims."""
import argparse,copy,json,sys,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,atomic_json,sha256

def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--self-collisions',choices=['on','off'],required=True);args=p.parse_args()
 enabled=args.self_collisions=='on'
 config={'task':'a1_collision_probe_v1','seed':72000,'num_envs':64,'self_collisions':enabled,
  'research_tags':['phase:P2','step:p2-00-collision-contract','purpose:implementation-check'],
  'cases':['supported_stance','suspended_random_joint_poses','lowered_body_ground_overlap'],'physics_dt':.005,
  'note':'Deliberate overlap and out-of-distribution states test sensors, not task feasibility.'}
 meta=begin_run(args.out,config,'probe')
 try:
  launch_app(False)
  import torch
  import omni.usd
  from pxr import PhysxSchema
  from parkour.sequential_task import SequentialCfg,SequentialEnv
  base=json.loads(Path('configs/p1-step02a-single-fl.json').read_text())
  cfg=SequentialCfg();cfg.scene.num_envs=64;cfg.seed=72000;cfg.sequence=copy.deepcopy(base['sequence']);cfg.sim.device='cuda:0';cfg.robot=copy.deepcopy(cfg.robot)
  cfg.robot.spawn.articulation_props.enabled_self_collisions=enabled
  e=SequentialEnv(cfg);e.reset()
  stage=omni.usd.get_context().get_stage();attrs=[]
  for prim in stage.Traverse():
   if str(prim.GetPath()).startswith('/World/envs/env_0/Robot') and prim.HasAPI(PhysxSchema.PhysxArticulationAPI):
    attrs.append({'prim':str(prim.GetPath()),'enabled':PhysxSchema.PhysxArticulationAPI(prim).GetEnabledSelfCollisionsAttr().Get()})
  assert attrs and all(x['enabled']==enabled for x in attrs),attrs
  nonfeet=[i for i in range(len(e.contacts.body_names)) if i not in e.contact_ids]
  def run_steps(target,steps):
   peaks=torch.zeros(64,len(e.contacts.body_names),device=e.device);min_z=torch.full((64,),float('inf'),device=e.device)
   for _ in range(steps):
    e.robot.set_joint_position_target(target);e.scene.write_data_to_sim();e.sim.step(render=False);e.scene.update(e.physics_dt)
    peaks=torch.maximum(peaks,e.contacts.data.net_forces_w.norm(dim=-1))
    min_z=torch.minimum(min_z,(e.robot.data.body_pos_w[:,:,2]-e.scene.env_origins[:,None,2]).amin(dim=1))
   return {'body_force_peak_N':peaks.tolist(),'min_body_center_z_m':min_z.tolist(),
    'any_contact_envs':int((peaks.amax(dim=1)>5).sum()),'nonfoot_contact_envs':int((peaks[:,nonfeet].amax(dim=1)>5).sum()),
    'foot_only_contact_envs':int(((peaks.amax(dim=1)>5)&(peaks[:,nonfeet].amax(dim=1)<=5)).sum())}
  supported=run_steps(e.robot.data.default_joint_pos,200)
  limits=e.robot.data.soft_joint_pos_limits[0].clone();assert torch.isfinite(limits).all()
  gen=torch.Generator(device=e.device).manual_seed(72000)
  poses=limits[:,0]+torch.rand(64,12,generator=gen,device=e.device)*(limits[:,1]-limits[:,0])
  def inject(z,joints):
   root=e.robot.data.default_root_state.clone();root[:,:3]=e.scene.env_origins;root[:,2]+=z;root[:,3:7]=torch.tensor([1.,0.,0.,0.],device=e.device);root[:,7:]=0
   e.robot.write_root_pose_to_sim(root[:,:7]);e.robot.write_root_velocity_to_sim(root[:,7:]);e.robot.write_joint_state_to_sim(joints,torch.zeros_like(joints));e.robot.reset();e.contacts.reset()
  inject(3.,poses);suspended=run_steps(poses,10)
  assert min(suspended['min_body_center_z_m'])>1.,'Ground separation not established'
  inject(.04,e.robot.data.default_joint_pos);overlap=run_steps(e.robot.data.default_joint_pos,10)
  result={'config':config,'usd_articulation_settings':attrs,'contact_body_names':e.contacts.body_names,
   'foot_names':e.foot_names,'joint_names':e.robot.joint_names,'sampled_joint_positions':poses.tolist(),
   'soft_joint_limits':limits.tolist(),'stance_calibration':e.calibration,
   'supported_stance':supported,'suspended_random_joint_poses':suspended,'lowered_body_ground_overlap':overlap,
   'limitation':'Net-force threshold is not exhaustive pairwise collision classification; cancellation and subthreshold contacts can be missed. Suspended cases are deliberate nonphysical initial overlaps.'}
  atomic_json(args.out/'collision-probe.json',result);meta['artifacts']={'collision-probe.json':sha256(args.out/'collision-probe.json')};finish_run(args.out,meta)
 except BaseException as exc:
  traceback.print_exc();finish_run(args.out,meta,exc)
if __name__=='__main__':main()
