"""Two persistent GPU workers: asynchronous scheduled foothold replanning assay.

File mailbox is local, atomic and bounded. Execution never waits for rollout.
Four surface goals are proposed; only a short branch receives physical validation.
"""
from pathlib import Path
import argparse,json,sys,time,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,sha256,atomic_json


def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--role',choices=['planner','executor'],required=True)
 p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--mailbox',type=Path,required=True);p.add_argument('--lifetime',type=float,default=180)
 p.add_argument('--fixed-plan',action='store_true')
 p.add_argument('--lead-steps',type=int,default=75);p.add_argument('--threads',type=int,default=4);p.add_argument('--full-horizon',action='store_true')
 args=p.parse_args();source=json.loads((args.source/'run.json').read_text())
 if source['status']!='SUCCEEDED':raise ValueError('Incomplete source')
 config=dict(source['config']);config['num_envs']=9 if args.role=='planner' else 1
 research_step='p3-59-actor-diagnostics' if args.fixed_plan else ('p3-58-full-horizon' if args.full_horizon or args.lead_steps>75 else 'p3-57-online-planner')
 config['research_tags']=['phase:P3','step:'+research_step,'role:'+args.role]
 meta=begin_run(args.out,config,'probe');args.mailbox.mkdir(parents=True,exist_ok=True)
 try:
  launch_app(False)
  import torch
  from parkour.learning import make_env,make_algorithm,read_checkpoint,restore
  from parkour.planner_states import PlannerStateRecorder,restore_airborne_state
  from parkour.candidate_plan import install_candidates
  torch.set_num_threads(args.threads)
  support=source.get('evaluation_support')
  env=make_env(config,evaluation_support=support);alg,norm=make_algorithm(config,env)
  state_config=dict(config)
  if support:state_config['terrain_contract']=support;meta['evaluation_support']=support
  checkpoint=Path(source['checkpoint']['path']);digest=sha256(checkpoint)
  if digest!=source['checkpoint']['sha256']:raise ValueError('Checkpoint mismatch')
  restore(read_checkpoint(checkpoint),config,alg,norm,env,False);alg.policy.eval();norm.eval()
  events=[];started=time.monotonic()
  if args.role=='planner':
   env.planner_rollout_only=True
   with torch.inference_mode():
    warm,_=env.reset()
    for _ in range(20):warm,_,_,_,_=env.step(alg.policy.act_inference(norm(warm['policy'])))
   atomic_json(args.mailbox/'ready.json',{'checkpoint_sha256':digest})
   seen=set()
   while time.monotonic()-started<args.lifetime and not (args.mailbox/'stop.json').exists():
    pending=sorted(set(args.mailbox.glob('request-*.json'))-seen)
    if not pending:time.sleep(.005);continue
    path=pending[0];seen.add(path);request=json.loads(path.read_text());t0=time.perf_counter()
    response={'id':request['id'],'activation_step':request['activation_step'],'accepted':False}
    try:
     with torch.inference_mode():
      restore_airborne_state(env,request['payload'],0,state_config,digest)
      raw=env._get_observations()['policy']
     failed=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
     with torch.inference_mode():
      # Predict the already committed plan up to the scheduled activation instant.
      for _ in range(request['lead_steps']):
       obs,_,term,trunc,_=env.step(alg.policy.act_inference(norm(raw)));raw=obs['policy'];failed|=term|trunc
      if bool(failed.any()):raise ValueError('Committed prefix fails before activation')
      predicted_root=(env.robot.data.root_pos_w[4]-env.scene.env_origins[4]).cpu().tolist()
      predicted_target=env.progress.target[4].cpu().tolist()
      predicted_articulation={'predicted_quaternion':env.robot.data.root_quat_w[4].cpu().tolist(),
        'predicted_joint_position':env.robot.data.joint_pos[4].cpu().tolist(),'predicted_velocity':env.robot.data.root_lin_vel_w[4].cpu().tolist()}
      start_surface=int(env.progress.target.max())+1
      contract=install_candidates(env,start_surface);raw=env._get_observations()['policy']
      plans=env.candidate_plan.clone();cost=torch.zeros(env.num_envs,device=env.device)
      reached=torch.zeros_like(failed);done=failed.clone();durations=torch.zeros(env.num_envs,device=env.device)
      branch_budget=150 if args.full_horizon else 15
      for branch_step in range(branch_budget):
       obs,_,term,trunc,extras=env.step(alg.policy.act_inference(norm(raw)));raw=obs['policy']
       active=~done
       metrics=extras['terminal_metrics']
       now_reached=(metrics['front_accepted_index']>=start_surface+3)&(metrics['rear_accepted_index']>=start_surface+3)&~metrics['failure']
       failed|=(term|trunc)&active&~now_reached
       reached|=now_reached&active
       speed=env.robot.data.root_lin_vel_w[:,:2].norm(dim=1)
       cost+=((speed-1.8).square()+.01*env.actions.square().sum(1))*env.step_dt*active
       durations+=active*env.step_dt;done|=failed|reached
       if args.full_horizon and bool(done.all()):break
      costs=cost/durations.clamp_min(env.step_dt)+failed.float()*1000
      if args.full_horizon:costs+=(~reached).float()*500
      winner=int(costs.argmin())
      if bool(failed[winner]) or (args.full_horizon and not bool(reached[winner])):raise ValueError('No validated branch')
      # Carry the existing plan unless a candidate improves the measured objective.
      if float(costs[4]-costs[winner])<.002:winner=4
      response.update(accepted=True,candidate_id=winner,costs=costs.cpu().tolist(),
        predicted_root=predicted_root,predicted_target=predicted_target,**predicted_articulation,
        start_surface=start_surface,plan=plans[winner].cpu().tolist(),contract=contract,
        physical_branch_seconds=(branch_step+1)*env.step_dt,prefix_seconds=request['lead_steps']*env.step_dt,
        full_horizon=args.full_horizon,horizon_reached=reached.cpu().tolist(),switch_cost_margin=.002)
    except (ValueError,RuntimeError) as error:response['rejection']=str(error)
    response['wall_seconds']=time.perf_counter()-t0;events.append(response)
    atomic_json(args.mailbox/('response-%04d.json'%request['id']),response)
  else:
   deadline=time.monotonic()+60
   while not args.fixed_plan and not (args.mailbox/'ready.json').exists():
    if time.monotonic()>deadline:raise RuntimeError('Planner startup timeout')
    time.sleep(.05)
   if not args.fixed_plan and json.loads((args.mailbox/'ready.json').read_text())['checkpoint_sha256']!=digest:raise ValueError('Planner policy mismatch')
   raw,_=env.reset();raw=raw['policy'];recorder=PlannerStateRecorder(env,state_config,digest)
   from concurrent.futures import ThreadPoolExecutor
   io=ThreadPoolExecutor(max_workers=1);writes=[]
   pending=None;request_id=0;last_request=-100;trace=[];compute=[];lateness=[]
   clock=time.perf_counter();result={};actor_saturation=[]
   with torch.inference_mode():
    for step in range(int(config['episode_seconds']/env.step_dt)):
     tick=time.perf_counter();lateness.append(max(0.,tick-(clock+step*env.step_dt)))
     if pending is not None and step>=pending['activation_step']:
      path=args.mailbox/('response-%04d.json'%pending['id'])
      event={'id':pending['id'],'step':step,'applied':False}
      if not path.exists():event['rejection']='deadline_missed'
      else:
       proposal=json.loads(path.read_text());event['planner_wall_seconds']=proposal['wall_seconds']
       if not proposal['accepted']:event['rejection']=proposal['rejection']
       else:
        from parkour.online_plan_contract import admission
        reason,err=admission(proposal,pending,step,(env.robot.data.root_pos_w[0]-env.scene.env_origins[0]).cpu().tolist(),env.progress.target[0].cpu().tolist(),{'quaternion':env.robot.data.root_quat_w[0].cpu().tolist(),'joint_position':env.robot.data.joint_pos[0].cpu().tolist(),'velocity':env.robot.data.root_lin_vel_w[0].cpu().tolist()})
        event['prediction_error_m']=err
        if reason:
         event['rejection']=reason
        else:
         env.candidate_plan=torch.tensor(proposal['plan'],device=env.device,dtype=env.plan.dtype)[None]
         raw=env._get_observations()['policy'];event.update(applied=True,candidate_id=proposal['candidate_id'],changed=proposal['candidate_id']!=4)
      events.append(event);pending=None
     if not args.fixed_plan and pending is None and step-last_request>=50 and int(env.progress.target.max())<env.plan.shape[1]-8:
      recorder.records=[];recorder.last_air=False;recorder.capture(step,torch.zeros(1,dtype=torch.bool,device=env.device))
      if recorder.records:
       pending={'id':request_id,'activation_step':step+args.lead_steps,'lead_steps':args.lead_steps,'payload':{'contract':recorder.contract,'states':recorder.records}}
       writes.append(io.submit(atomic_json,args.mailbox/('request-%04d.json'%request_id),pending));request_id+=1;last_request=step
     trace.append({'step':step,'root':env.robot.data.root_state_w[0].cpu().tolist(),'q':env.robot.data.joint_pos[0].cpu().tolist(),
       'dq':env.robot.data.joint_vel[0].cpu().tolist(),'target':env.progress.target[0].cpu().tolist(),
       'targets_w':env.targets[0].cpu().tolist(),'forces':env.contacts.data.net_forces_w[0,env.contact_ids,2].cpu().tolist(),
       'contact_on':env.contact_on[0].cpu().tolist(),'actions':env.actions[0].cpu().tolist(),'accepted':env.progress.accepted[0].cpu().tolist(),'jumps':int(env.flights.count[0])})
     mean=alg.policy.act_inference(norm(raw))
     actor_saturation.append((mean.abs()>.98).float().mean().item())
     obs,_,term,trunc,extras=env.step(mean);raw=obs['policy']
     compute.append(time.perf_counter()-tick)
     if bool(term[0]|trunc[0]):
      result={k:v[0].item() for k,v in extras['terminal_metrics'].items() if v[0].numel()==1};break
     remaining=clock+(step+1)*env.step_dt-time.perf_counter()
     if remaining>0:time.sleep(remaining)
   execution_wall=time.perf_counter()-clock
   if pending is not None:events.append({'id':pending['id'],'applied':False,'rejection':'episode_ended_before_activation'})
   for write in writes:write.result()
   io.shutdown()
   atomic_json(args.mailbox/'stop.json',{'finished':True})
   atomic_json(args.out/'state-playback.json',{'artifact_type':'recorded_state_playback_source','frames':trace})
   atomic_json(args.out/'execution.json',{'result':result,'sim_seconds':len(trace)*env.step_dt,'wall_seconds':execution_wall,
     'compute_max_seconds':max(compute),'compute_median_seconds':sorted(compute)[len(compute)//2],
     'compute_p95_seconds':sorted(compute)[int(.95*(len(compute)-1))],'compute_deadline_misses':sum(x>env.step_dt for x in compute),
     'schedule_lateness_max_seconds':max(lateness),'requests':request_id,'events':events,'mean_actor_saturation_fraction':sum(actor_saturation)/len(actor_saturation),
     'lead_seconds':args.lead_steps*env.step_dt,'scope':'One development episode, asynchronous candidate choice on fixed surface route. See each response for actual physical branch horizon; runtime and statistical generalization remain unverified.'})
  atomic_json(args.out/'planner-events.json',events)
  meta['artifacts']={p.name:sha256(p) for p in args.out.glob('*.json') if p.name not in ('run.json','config.json')};meta['checkpoint']={'path':str(checkpoint),'sha256':digest}
  finish_run(args.out,meta)
 except BaseException as error:
  if args.role=='executor':atomic_json(args.mailbox/'stop.json',{'error':repr(error)})
  finish_run(args.out,meta,error)
if __name__=='__main__':main()
