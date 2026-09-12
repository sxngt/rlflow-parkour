"""Bounded, explicit airborne state records for subsequent clone validation.

No PhysX solver checkpoint claim. Flight-only selection avoids claiming that
contact warm-start caches are represented by joint/root coordinates.
"""
import hashlib,json
import torch
from parkour.runtime import atomic_json

ENV_FIELDS=('actions','previous_actions','contact_on','episode_length_buf','final_hold','current_valid','current_error',
 'active_motion_steps','travel_motion_steps','travel_jumps','travel_airborne','new_gap_credit','error_sum','sample_count','reward_sum')
PROGRESS_FIELDS=('target','accepted','hold','age')
FLIGHT_FIELDS=('air','duration','start_z','peak_z','up','bad','had_support','previous_z','count','airborne_count')
GAP_FIELDS=('index','start','previous','eligible','paid')

def environment_hash(config):
    c=dict(config)
    for key in ('iterations','num_envs','research_tags'):c.pop(key,None)
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

class PlannerStateRecorder:
    def __init__(self,env,config,checkpoint_sha):
        self.env=env;self.records=[];self.last_air=False
        self.contract={'schema_version':1,'environment_hash':environment_hash(config),'checkpoint_sha256':checkpoint_sha,
            'physics_dt_s':env.physics_dt,'control_dt_s':env.step_dt,'source_env':0,
            'scope':'Airborne root/joint/controller state only; not a PhysX solver checkpoint. Restore and prediction fidelity must be validated before planning.'}
    def capture(self,step,done):
        if len(self.records)>=4 or bool(done[0]):return
        e=self.env;air=bool(e.flights.air[0])
        onset=air and not self.last_air;self.last_air=air
        if not onset:return
        force=e.contacts.data.net_forces_w[0]
        if not bool(torch.isfinite(force).all()):return
        if float(force[e.contact_ids].norm(dim=-1).max())>=2 or float(force[e.nonfoot_ids].norm(dim=-1).max())>1e-3:return
        def values(obj,names):return {k:getattr(obj,k)[0].detach().cpu().tolist() for k in names}
        root=e.robot.data.root_state_w[0].clone();root[:3]-=e.scene.env_origins[0]
        active_plan=getattr(e,'candidate_plan',None)
        active_plan=e.plan if active_plan is None else active_plan[0]
        self.records.append({'target_plan':active_plan.cpu().tolist(),'control_step':step,'sim_seconds':step*e.step_dt,'root_state_local':root.cpu().tolist(),
            'joint_position':e.robot.data.joint_pos[0].cpu().tolist(),'joint_velocity':e.robot.data.joint_vel[0].cpu().tolist(),
            'foot_position_local':(e.robot.data.body_pos_w[0,e.foot_ids]-e.scene.env_origins[0]).cpu().tolist(),
            'environment':values(e,ENV_FIELDS),'progress':values(e.progress,PROGRESS_FIELDS),'flight':values(e.flights,FLIGHT_FIELDS),
            'gap_credit':values(e.gap_credit,GAP_FIELDS) if e.gap_credit is not None else None})
    def close(self,out):atomic_json(out/'planner-states.json',{'contract':self.contract,'states':self.records})


def restore_airborne_state(env,payload,index,config,checkpoint_sha):
    contract=payload['contract']
    if contract['schema_version']!=1 or contract['environment_hash']!=environment_hash(config) or contract['checkpoint_sha256']!=checkpoint_sha:
        raise ValueError('Planner state contract mismatch')
    if contract['physics_dt_s']!=env.physics_dt or contract['control_dt_s']!=env.step_dt:raise ValueError('Planner clock mismatch')
    state=payload['states'][index]
    if not state['flight']['air'] or any(state['environment']['contact_on']):raise ValueError('Only clean airborne state restoration supported')
    def fill(obj,record,fields):
        if set(record)!=set(fields):raise ValueError('Incomplete controller state')
        for k in fields:
            target=getattr(obj,k);value=torch.as_tensor(record[k],dtype=target.dtype,device=target.device)
            if tuple(value.shape)!=tuple(target.shape[1:]) or (value.is_floating_point() and not bool(torch.isfinite(value).all())):raise ValueError('Invalid state tensor: '+k)
            target.copy_(value.expand_as(target))
    env.candidate_plan=env.plan[None].repeat(env.num_envs,1,1,1,1)
    env.reset()
    root=torch.tensor(state['root_state_local'],device=env.device).repeat(env.num_envs,1);root[:,:3]+=env.scene.env_origins
    q=torch.tensor(state['joint_position'],device=env.device).repeat(env.num_envs,1)
    dq=torch.tensor(state['joint_velocity'],device=env.device).repeat(env.num_envs,1)
    if root.shape!=(env.num_envs,13) or q.shape!=(env.num_envs,12) or dq.shape!=q.shape or not bool(torch.isfinite(torch.cat([root,q,dq],dim=1)).all()):raise ValueError('Invalid articulation state')
    env.robot.write_root_state_to_sim(root);env.robot.write_joint_state_to_sim(q,dq)
    fill(env,state['environment'],ENV_FIELDS);fill(env.progress,state['progress'],PROGRESS_FIELDS);fill(env.flights,state['flight'],FLIGHT_FIELDS)
    if (env.gap_credit is None)!=(state['gap_credit'] is None):raise ValueError('Gap state mismatch')
    if env.gap_credit is not None:fill(env.gap_credit,state['gap_credit'],GAP_FIELDS)
    plan=torch.as_tensor(state.get('target_plan',env.plan),device=env.device,dtype=env.plan.dtype)
    if plan.shape!=env.plan.shape or not bool(torch.isfinite(plan).all()):raise ValueError('Invalid restored goal plan')
    local=torch.einsum('sji,sgfj->sgfi',env.surface_rotations,plan.permute(1,0,2,3)-env.surface_centers[:,None,None,:])
    if not bool(((local[...,:2].abs()<=env.surface_halves[:,None,None,:]+1e-6).all(dim=-1)&(local[...,2]>=0)&(local[...,2]<=.04)).all()):raise ValueError('Restored goals violate surface margins')
    env.candidate_plan=plan[None].repeat(env.num_envs,1,1,1,1)
    env.contacts.reset();env._sync_targets();env.sim.forward()
    # Read-back is necessary, but does not validate future contact dynamics.
    expected=torch.tensor(state['foot_position_local'],device=env.device)
    error=float((env.robot.data.body_pos_w[:,env.foot_ids]-env.scene.env_origins[:,None,:]-expected).abs().max())
    if error>.002:raise RuntimeError('Restored foot geometry differs by '+str(error)+'m')
    return {'foot_geometry_max_error_m':error,'scope':'Articulation/controller readback only; predictive rollout fidelity not yet validated'}
