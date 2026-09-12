"""Physics-rate traces for independent front/rear targets, without legacy phases."""
import numpy as np
from parkour.runtime import atomic_json
class ContinuousDiagnostics:
    def __init__(self,env,done):
        self.env,self.done=env,done;self.samples=[];self.elapsed=0.;self.original=env.scene.update
        def update(dt):
            self.original(dt)
            if dt<=0:return
            self.elapsed+=dt
            cpu=lambda x:x.detach().cpu().numpy().copy()
            e=env
            self.samples.append({'time':self.elapsed,'valid':cpu(~done),
                'root_pos':cpu(e.robot.data.root_pos_w-e.scene.env_origins),'root_velocity':cpu(e.robot.data.root_lin_vel_b),
                'root_velocity_world':cpu(e.robot.data.root_lin_vel_w),
                'joint_position':cpu(e.robot.data.joint_pos),
                'joint_velocity':cpu(e.robot.data.joint_vel),
                'joint_position_target':cpu(e.robot.data.joint_pos_target),
                'computed_torque':cpu(e.robot.data.computed_torque),
                'applied_torque':cpu(e.robot.data.applied_torque),
                'nonfoot_force_max':cpu(e.contacts.data.net_forces_w[:,e.nonfoot_ids].norm(dim=-1).amax(dim=1)),
                'measured_jump_count':cpu(e.flights.count),
                'foot_pos':cpu(e.robot.data.body_pos_w[:,e.foot_ids]-e.scene.env_origins[:,None,:]),
                'force':cpu(e.contacts.data.net_forces_w[:,e.contact_ids]),'action':cpu(e.actions),
                'target_xyz':cpu(e.targets-e.scene.env_origins[:,None,:]),'target_indices':cpu(e.progress.target),
                'accepted_indices':cpu(e.progress.accepted),'target_age_steps':cpu(e.progress.age)})
        env.scene.update=update
    def close(self,out,scenario_ids):
        self.env.scene.update=self.original
        arrays={k:np.stack([s[k] for s in self.samples]) for k in self.samples[0]}
        np.savez_compressed(out/'motion-trace.npz',**arrays)
        summaries=[]
        for i,scenario in enumerate(scenario_ids):
            valid=arrays['valid'][:,i]
            xy=arrays['root_pos'][valid,i,:2]
            summaries.append({'scenario_id':scenario,'duration_s':float(valid.sum()*self.env.physics_dt),
                'root_xy_displacement_m':float(np.linalg.norm(xy[-1]-xy[0])) if len(xy)>1 else 0.,
                'root_xy_path_length_m':float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()) if len(xy)>1 else 0.})
        report={'schema_version':4,'contract':'continuous_pair_trace_v1','physics_dt_s':self.env.physics_dt,
                'joint_names':list(self.env.robot.joint_names),
                'actuator_trace_scope':'Joint positions/targets in rad, velocities in rad/s; computed and applied actuator torques in Nm. Applied torque is a simulator actuator output, not measured hardware torque.',
                'results':summaries,'mean_root_xy_displacement_m':float(np.mean([s['root_xy_displacement_m'] for s in summaries])),
                'mean_root_xy_path_length_m':float(np.mean([s['root_xy_path_length_m'] for s in summaries])),
                'distance_scope':'Measured between first and last valid physics samples; path length includes oscillation and is not route completion',
                'scenario_ids':scenario_ids,'samples_per_episode':arrays['valid'].sum(axis=0).tolist(),
                'scope':'First episode per environment; front/rear target indices are pre-control-update physics samples'}
        atomic_json(out/'diagnostics.json',report);return report
