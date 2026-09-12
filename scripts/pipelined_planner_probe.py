"""Overlap physical foothold planning with execution using verified forecast states.

Initial four-step planning precedes execution. Later branches start from cached
future airborne controller states; every activation checks the actual state.
A rejected forecast stops further pipeline updates; nominal goals remain as an
explicit fixed-plan fallback. This is a development assay, not a safety system.
"""
from pathlib import Path
import argparse,json,sys,time,traceback,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from parkour.runtime import begin_run,finish_run,launch_app,atomic_json,sha256

def plan_hash(plan):return hashlib.sha256(json.dumps(plan,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--role',choices=['planner','executor'],required=True)
 p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mailbox',type=Path,required=True)
 p.add_argument('--fixed-initial-plan',type=Path,help='Executor-only matched control: retain this initial plan without later updates')
 a=p.parse_args()
 if a.fixed_initial_plan and a.role!='executor':p.error('Fixed initial plan is executor-only')
 source=json.loads((a.source/'run.json').read_text())
 if source['status']!='SUCCEEDED':raise ValueError('Incomplete source')
 c=dict(source['config']);c['num_envs']=9 if a.role=='planner' else 1;c['research_tags']=['phase:P3','step:p3-71-pipelined-planner','role:'+a.role]
 meta=begin_run(a.out,c,'probe');a.mailbox.mkdir(parents=True,exist_ok=True)
 try:
  launch_app(False)
  import torch
  from parkour.learning import make_env,make_algorithm,restore,read_checkpoint
  from parkour.planner_states import capture_prediction_state,restore_airborne_state
  from parkour.candidate_plan import install_candidates
  from parkour.online_plan_contract import admission
  torch.set_num_threads(1);support=source.get('evaluation_support',c['terrain_contract'])
  env=make_env(c,evaluation_support=support);alg,norm=make_algorithm(c,env)
  checkpoint=Path(source['checkpoint']['path']);digest=sha256(checkpoint)
  if digest!=source['checkpoint']['sha256']:raise ValueError('Policy mismatch')
  restore(read_checkpoint(checkpoint),c,alg,norm,env,False);alg.policy.eval();norm.eval()
  state_config=dict(c);state_config['terrain_contract']=support
  meta.update(checkpoint={'path':str(checkpoint),'sha256':digest},evaluation_support=support)
  events=[]
  if a.role=='planner':
   env.planner_rollout_only=True;payload=None;previous_plan_hash=None
   for phase in range(8):
    t0=time.perf_counter()
    with torch.inference_mode():
     if payload is None:
      env.candidate_plan=env.plan[None].repeat(9,1,1,1,1);env.reset();origin=0;start_surface=1
     else:
      restore_airborne_state(env,payload,0,state_config,digest);origin=payload['states'][0]['control_step'];start_surface=int(env.progress.target.max())+1
     if start_surface+5>env.plan.shape[1]:
      events.append({'id':phase,'status':'no_remaining_four_surface_window'});break
     contract=install_candidates(env,start_surface);plans=env.candidate_plan.clone();raw=env._get_observations()['policy']
     done=torch.zeros(9,dtype=torch.bool,device=env.device);failed=done.clone();reached=done.clone();cost=torch.zeros(9,device=env.device);duration=cost.clone();caches=[None]*9
     for tick in range(200):
      # Retain the latest available future flight, giving the next worker time
      # to finish. No reward/flight counters are fabricated by this capture.
      if tick*env.step_dt>=1.4 and tick%2==0:
       force=env.contacts.data.net_forces_w
       clean=(force[:,env.contact_ids].norm(dim=-1).amax(1)<2)&(force[:,env.nonfoot_ids].norm(dim=-1).amax(1)<=1e-3)&~env.contact_on.any(1)&~done
       for index in clean.nonzero().flatten().tolist():
        value=capture_prediction_state(env,state_config,digest,index,origin+tick)
        if value is not None:caches[index]=value
      obs,_,term,trunc,extras=env.step(alg.policy.act_inference(norm(raw)));raw=obs['policy'];m=extras['terminal_metrics'];active=~done
      now=(m['front_accepted_index']>=start_surface+3)&(m['rear_accepted_index']>=start_surface+3)&~m['failure']
      failed|=(term|trunc)&active&~now;reached|=now&active
      speed=env.robot.data.root_lin_vel_w[:,:2].norm(dim=1)
      cost+=((speed-1.8).square()+.01*env.actions.square().sum(1))*active*env.step_dt;duration+=active*env.step_dt;done|=failed|reached
      if bool(done.all()):break
     scores=cost/duration.clamp_min(env.step_dt)+failed.float()*1000+(~reached).float()*500
     winner=int(scores.argmin())
     if not bool(reached[winner]):
      events.append({'id':phase,'status':'no_feasible_four_surface_candidate','scores':scores.cpu().tolist()});break
     if bool(reached[4]) and float(scores[4]-scores[winner])<.002:winner=4
     plan=plans[winner].cpu().tolist();next_payload=caches[winner]
     proposal={'id':phase,'activation_step':origin,'accepted':True,'candidate_id':winner,'plan':plan,'plan_hash':plan_hash(plan),
       'parent_plan_hash':previous_plan_hash,'checkpoint_sha256':digest,'contract':contract,'start_surface':start_surface,
       'horizon_reached':reached.cpu().tolist(),'scores':scores.cpu().tolist(),'physical_rollout_seconds':(tick+1)*env.step_dt,
       'next_activation_step':None if next_payload is None else next_payload['states'][0]['control_step']}
     if payload is not None:
      state=payload['states'][0];root=state['root_state_local']
      proposal.update(predicted_root=root[:3],predicted_quaternion=root[3:7],predicted_velocity=root[7:10],predicted_joint_position=state['joint_position'],predicted_target=state['progress']['target'])
     proposal['wall_seconds']=time.perf_counter()-t0
    events.append({k:v for k,v in proposal.items() if k!='plan'})
    atomic_json(a.out/('phase-%02d.json'%phase),{'proposal':proposal,'next_forecast':next_payload})
    atomic_json(a.mailbox/('phase-%02d.json'%phase),proposal)
    deadline=time.monotonic()+60;ack_path=a.mailbox/('ack-%02d.json'%phase)
    while not ack_path.exists() and not (a.mailbox/'stop.json').exists():
     if time.monotonic()>deadline:raise TimeoutError('Executor acknowledgement')
     time.sleep(.005)
    if not ack_path.exists():break
    ack=json.loads(ack_path.read_text());events.append({'id':phase,'ack':ack})
    if not ack['applied'] or next_payload is None:break
    payload=next_payload;previous_plan_hash=proposal['plan_hash']
   atomic_json(a.mailbox/'planner-finished.json',{'finished':True})
  else:
   from concurrent.futures import ThreadPoolExecutor
   deadline=time.monotonic()+90;initial=a.fixed_initial_plan or a.mailbox/'phase-00.json'
   while not initial.exists():
    if (a.mailbox/'planner-finished.json').exists():raise RuntimeError('Initial planning found no feasible candidate')
    if time.monotonic()>deadline:raise TimeoutError('Initial plan')
    time.sleep(.01)
   first=json.loads(initial.read_text())
   if first['checkpoint_sha256']!=digest or first['plan_hash']!=plan_hash(first['plan']):raise ValueError('Initial plan identity mismatch')
   env.candidate_plan=torch.tensor(first['plan'],device=env.device,dtype=env.plan.dtype)[None];raw,_=env.reset();raw=raw['policy']
   with torch.inference_mode():
    for _ in range(10):alg.policy.act_inference(norm(raw))
   current_hash=first['plan_hash'];next_phase=1;activation=None if a.fixed_initial_plan else first['next_activation_step'];io=ThreadPoolExecutor(max_workers=1);writes=[]
   atomic_json(a.mailbox/'ack-00.json',{'applied':True,'step':0,'plan_hash':current_hash})
   from parkour.execution_trace import ExecutionTrace
   trace_buffer=ExecutionTrace(int(c['episode_seconds']/env.step_dt));compute=[];lateness=[];result={};clock=time.perf_counter()
   with torch.inference_mode():
    for step in range(int(c['episode_seconds']/env.step_dt)):
     tick=time.perf_counter();lateness.append(max(0.,tick-(clock+step*env.step_dt)))
     if activation is not None and step>=activation:
      path=a.mailbox/('phase-%02d.json'%next_phase);event={'id':next_phase,'step':step,'applied':False}
      if not path.exists():event['rejection']='deadline_missed'
      else:
       proposal=json.loads(path.read_text());event['planner_wall_seconds']=proposal['wall_seconds']
       if proposal['parent_plan_hash']!=current_hash or proposal['checkpoint_sha256']!=digest or proposal['plan_hash']!=plan_hash(proposal['plan']):event['rejection']='plan_identity_mismatch'
       else:
        reason,error=admission(proposal,{'id':next_phase,'activation_step':activation},step,
         (env.robot.data.root_pos_w[0]-env.scene.env_origins[0]).cpu().tolist(),env.progress.target[0].cpu().tolist(),
         {'quaternion':env.robot.data.root_quat_w[0].cpu().tolist(),'joint_position':env.robot.data.joint_pos[0].cpu().tolist(),'velocity':env.robot.data.root_lin_vel_w[0].cpu().tolist()})
        if bool(env.contact_on[0].any()):reason='contact_mode_mismatch'
        event['prediction_error_m']=error
        if reason:event['rejection']=reason
        else:
         env.candidate_plan=torch.tensor(proposal['plan'],device=env.device,dtype=env.plan.dtype)[None];raw=env._get_observations()['policy'];current_hash=proposal['plan_hash']
         event.update(applied=True,candidate_id=proposal['candidate_id'],changed=proposal['candidate_id']!=4)
      events.append(event);writes.append(io.submit(atomic_json,a.mailbox/('ack-%02d.json'%next_phase),event))
      activation=proposal['next_activation_step'] if event['applied'] else None;next_phase+=1
     trace_buffer.capture(env)
     obs,_,term,trunc,extras=env.step(alg.policy.act_inference(norm(raw)));raw=obs['policy'];compute.append(time.perf_counter()-tick)
     if bool(term[0]|trunc[0]):
      result={k:v[0].item() for k,v in extras['terminal_metrics'].items() if v[0].numel()==1};break
     remaining=clock+(step+1)*env.step_dt-time.perf_counter()
     if remaining>0:time.sleep(remaining)
   wall=time.perf_counter()-clock
   trace=trace_buffer.serialize()
   for write in writes:write.result()
   io.shutdown();atomic_json(a.mailbox/'stop.json',{'finished':True})
   atomic_json(a.out/'state-playback.json',{'artifact_type':'recorded_state_playback_source','frames':trace})
   atomic_json(a.out/'execution.json',{'result':result,'fixed_initial_plan_control':bool(a.fixed_initial_plan),'initial_candidate':first['candidate_id'],'initial_planning_seconds':first['wall_seconds'],'events':events,
    'sim_seconds':len(trace)*env.step_dt,'wall_seconds':wall,'telemetry_mode':'bounded_device_buffer','compute_max_seconds':max(compute),'compute_p95_seconds':sorted(compute)[int(.95*(len(compute)-1))],
    'compute_deadline_misses':sum(x>env.step_dt for x in compute),'schedule_lateness_max_seconds':max(lateness),
    'scope':'Initial four-surface planning before execution; later forecast-cache activations require matching actual pose, joints, velocity, contact and plan identity. Rejection retains nominal fixed-plan fallback; no recovery or statistical success claim.'})
  atomic_json(a.out/'planner-events.json',events);meta['artifacts']={p.name:sha256(p) for p in a.out.glob('*.json') if p.name not in ('run.json','config.json')};finish_run(a.out,meta)
 except BaseException as error:
  traceback.print_exc();atomic_json(a.mailbox/'stop.json',{'error':repr(error)});finish_run(a.out,meta,error)
if __name__=='__main__':main()
