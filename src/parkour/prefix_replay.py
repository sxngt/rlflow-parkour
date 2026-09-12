"""Reconstruct a short observed prefix by action replay; audit before branching.

This deliberately avoids claiming a restored PhysX solver snapshot. It is a
costly research baseline for planning from a moving state, not a real-time path.
"""
import json
import numpy as np
import torch
from parkour.runtime import sha256

class PrefixReplay:
    def __init__(self,env,source,steps,checkpoint,config):
        run=json.loads((source/'run.json').read_text());trace=source/'motion-trace.npz'
        if run['status']!='SUCCEEDED' or sha256(trace)!=run['artifacts']['motion-trace.npz']:raise ValueError('Invalid source trace')
        if checkpoint is None or sha256(checkpoint)!=run['checkpoint']['sha256']:raise ValueError('Prefix checkpoint mismatch')
        a=dict(config);b=dict(run['config'])
        for c in (a,b):c.pop('num_envs',None);c.pop('research_tags',None)
        if a!=b or run.get('shared_course_override') or run.get('candidate_plan_contract'):raise ValueError('Prefix physical/config contract mismatch')
        data=np.load(trace);self.trace={k:data[k] for k in data.files};data.close()
        if not 1<=steps<=200 or len(self.trace['valid'])<=steps*4 or not self.trace['valid'][:steps*4+1,0].all():raise ValueError('Invalid prefix length')
        replay_file=source/'replay.json'
        if sha256(replay_file)!=run['artifacts']['replay.json']:raise ValueError('Invalid source replay')
        rows=json.loads(replay_file.read_text())['trace']
        matches=[row for row in rows if abs(row['sim_time_s']-steps*env.step_dt)<1e-7]
        if len(matches)!=1:raise ValueError('Prefix requires a recorded pose at its exact time')
        self.root_state=matches[0]['root_state_w']
        if len(self.root_state)!=13:raise ValueError('Prefix requires single-robot follow recording')
        self.steps=steps;self.env=env
        self.actions=torch.tensor(self.trace['action'][:steps*4:4,0],device=env.device)
        self.metadata={'source':str(source),'trace_sha256':sha256(trace),'control_steps':steps,'sim_seconds':steps*env.step_dt,
            'scope':'Replayed applied actions from calibrated start; validation required before branch; no real-time or bitwise replay claim'}
    def action(self,step):return self.actions[step][None].expand(self.env.num_envs,-1)
    def validate(self):
        e=self.env;i=self.steps*4-1
        def maximum(value,reference):return float((value-torch.tensor(reference,device=e.device)).abs().max())
        errors={'root_position_m':maximum(e.robot.data.root_pos_w-e.scene.env_origins,self.trace['root_pos'][i,0]),
            'root_velocity_mps':maximum(e.robot.data.root_lin_vel_w,self.trace['root_velocity_world'][i,0]),
            'joint_position_rad':maximum(e.robot.data.joint_pos,self.trace['joint_position'][i,0]),
            'joint_velocity_rad_s':maximum(e.robot.data.joint_vel,self.trace['joint_velocity'][i,0])}
        q=torch.tensor(self.root_state[3:7],device=e.device)
        similarity=(e.robot.data.root_quat_w*q).sum(dim=1).abs().clamp(max=1.)
        errors['root_orientation_rad']=float((2*torch.acos(similarity)).max())
        errors['root_angular_velocity_rad_s']=maximum(e.robot.data.root_ang_vel_w,self.root_state[10:13])
        targets=torch.tensor(self.trace['target_indices'][i+1,0],device=e.device)
        errors['target_indices_equal']=bool((e.progress.target==targets).all())
        self.metadata['errors']=errors
        self.metadata['tolerances']={'root_position_m':.01,'root_velocity_mps':.15,'joint_position_rad':.02,'joint_velocity_rad_s':.5,'root_orientation_rad':.02,'root_angular_velocity_rad_s':.15}
        valid=errors['target_indices_equal'] and all(errors[k]<=v for k,v in self.metadata['tolerances'].items())
        self.metadata['validated']=valid
        return valid
