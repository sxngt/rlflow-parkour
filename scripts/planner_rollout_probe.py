"""Validate airborne articulation/controller cloning and four-step policy branches."""
from pathlib import Path
import argparse,json,sys,time,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,sha256,atomic_json

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--snapshot-index',type=int,default=0)
 p.add_argument('--lean',action='store_true',help='Skip reward and flight accounting; retain identical policy observations/actions/contact/failure gates')
 p.add_argument('--profile',action='store_true');p.add_argument('--uncapped-kit-loop',action='store_true')
 args=p.parse_args();source=json.loads((args.source/'run.json').read_text())
 for name in ('planner-states.json','motion-trace.npz'):
  if source['status']!='SUCCEEDED' or sha256(args.source/name)!=source['artifacts'][name]:raise ValueError('Source artifact mismatch')
 config=dict(source['config']);config['num_envs']=72;config['research_tags']=['phase:P3','step:p3-54-airborne-branches','purpose:state-clone-validation']
 meta=begin_run(args.out,config,'probe')
 try:
  launch_app(False)
  import torch,numpy as np
  from parkour.learning import make_env,make_algorithm,read_checkpoint,restore
  from parkour.planner_states import restore_airborne_state
  from parkour.candidate_plan import install_candidates
  torch.set_num_threads(4)
  support=source.get('evaluation_support')
  env=make_env(config,evaluation_support=support);alg,norm=make_algorithm(config,env)
  state_config=dict(config)
  if support:state_config['terrain_contract']=support;meta['evaluation_support']=support
  import carb.settings
  settings=carb.settings.get_settings();previous_rate_limit=settings.get('/app/runLoops/main/rateLimitEnabled')
  if args.uncapped_kit_loop:settings.set_bool('/app/runLoops/main/rateLimitEnabled',False)
  checkpoint=Path(source['checkpoint']['path']);data=read_checkpoint(checkpoint)
  if sha256(checkpoint)!=source['checkpoint']['sha256']:raise ValueError('Source policy mismatch')
  restore(data,config,alg,norm,env,False);alg.policy.eval();norm.eval()
  payload=json.loads((args.source/'planner-states.json').read_text())
  if not 0<=args.snapshot_index<len(payload['states']):raise ValueError('No requested clean airborne snapshot')
  readback=restore_airborne_state(env,payload,args.snapshot_index,state_config,sha256(checkpoint))
  env.planner_rollout_only=args.lean
  initial_step=payload['states'][args.snapshot_index]['control_step']
  # Preserve the current airborne landing; branch only later contact goals.
  start_surface=int(env.progress.target[:,0].max())+1
  contract=install_candidates(env,start_surface);target=start_surface+3
  atomic_json(args.out/'source-state.json',{'contract':payload['contract'],'state':payload['states'][args.snapshot_index]})
  raw=env._get_observations()['policy'];done=torch.zeros(72,dtype=torch.bool,device=env.device);records=[None]*72
  with np.load(args.source/'motion-trace.npz') as trace:reference={k:trace[k] for k in ('valid','root_pos','root_velocity_world','joint_position')}
  predicted=[];started=time.perf_counter()
  import cProfile
  profiler=cProfile.Profile() if args.profile else None
  if profiler:profiler.enable()
  with torch.inference_mode():
   for step in range(200):
    obs,reward,term,trunc,extras=env.step(alg.policy.act_inference(norm(raw)));raw=obs['policy']
    metrics=extras['terminal_metrics'];reached=(metrics['front_accepted_index']>=target)&(metrics['rear_accepted_index']>=target)&~metrics['failure']
    newly=(reached|term|trunc)&~done
    for i in newly.nonzero().flatten().tolist():records[i]={'env':i,'candidate_id':i%9,'horizon_reached':bool(reached[i]),'failure':bool(metrics['failure'][i]),'seconds':(step+1)*env.step_dt,'front_accepted_index':int(metrics['front_accepted_index'][i]),'rear_accepted_index':int(metrics['rear_accepted_index'][i])}
    index=(initial_step+step)*4+3
    if step<10 and index<len(reference['valid']) and reference['valid'][index,0] and not bool((done|newly)[4]):
     root=env.robot.data.root_pos_w[4]-env.scene.env_origins[4]
     predicted.append({'seconds':(step+1)*env.step_dt,
       'root_position_max_error_m':float((root-torch.tensor(reference['root_pos'][index,0],device=env.device)).abs().max()),
       'root_velocity_max_error_mps':float((env.robot.data.root_lin_vel_w[4]-torch.tensor(reference['root_velocity_world'][index,0],device=env.device)).abs().max()),
       'joint_position_max_error_rad':float((env.robot.data.joint_pos[4]-torch.tensor(reference['joint_position'][index,0],device=env.device)).abs().max())})
    done|=newly
    if bool(done.all()):break
  if profiler:
   profiler.disable()
   import pstats,io
   output=io.StringIO();pstats.Stats(profiler,stream=output).sort_stats('cumtime').print_stats(35)
   (args.out/'rollout-profile.txt').write_text(output.getvalue())
  for i,r in enumerate(records):
   if r is None:records[i]={'env':i,'candidate_id':i%9,'horizon_reached':False,'failure':False,'rollout_budget_exhausted':True,'seconds':200*env.step_dt}
  results=[{'candidate_id':i,'horizon_reached':sum(r['horizon_reached'] for r in records if r['candidate_id']==i),'replicas':8} for i in range(9)]
  report={'contract':contract,'source':str(args.source),'checkpoint_sha256':sha256(checkpoint),'source_control_step':initial_step,'required_surface_index':target,
    'lean_rollout':args.lean,'kit_rate_limit_before':previous_rate_limit,'uncapped_kit_loop':args.uncapped_kit_loop,'prediction_branch_env':4,
    'readback':readback,'zero_offset_short_horizon_prediction_errors':predicted,'results':results,'episodes':records,'rollout_wall_seconds':time.perf_counter()-started,
    'scope':'Cold airborne clone physical assay; current landing committed. Predictions reported, no automatic real-time feasibility certification or winner deployment.'}
  atomic_json(args.out/'planner-rollouts.json',report)
  meta['artifacts']={name:sha256(args.out/name) for name in ('source-state.json','planner-rollouts.json')};meta['planner_assay']=report['scope']
  if args.profile:meta['artifacts']['rollout-profile.txt']=sha256(args.out/'rollout-profile.txt')
  finish_run(args.out,meta)
 except BaseException as error:finish_run(args.out,meta,error);traceback.print_exc();raise
if __name__=='__main__':main()
