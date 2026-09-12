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
                'foot_pos':cpu(e.robot.data.body_pos_w[:,e.foot_ids]-e.scene.env_origins[:,None,:]),
                'force':cpu(e.contacts.data.net_forces_w[:,e.contact_ids]),'action':cpu(e.actions),
                'target_xyz':cpu(e.targets-e.scene.env_origins[:,None,:]),'target_indices':cpu(e.progress.target),
                'accepted_indices':cpu(e.progress.accepted),'target_age_steps':cpu(e.progress.age)})
        env.scene.update=update
    def close(self,out,scenario_ids):
        self.env.scene.update=self.original
        arrays={k:np.stack([s[k] for s in self.samples]) for k in self.samples[0]}
        np.savez_compressed(out/'motion-trace.npz',**arrays)
        report={'schema_version':2,'contract':'continuous_pair_trace_v1','physics_dt_s':self.env.physics_dt,
                'scenario_ids':scenario_ids,'samples_per_episode':arrays['valid'].sum(axis=0).tolist(),
                'scope':'First episode per environment; front/rear target indices are pre-control-update physics samples'}
        atomic_json(out/'diagnostics.json',report);return report
