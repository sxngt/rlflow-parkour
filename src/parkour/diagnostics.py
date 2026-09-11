"""Read-only physics-step capture. First episodes only; no reset samples in metrics."""
from __future__ import annotations
import numpy as np
import torch
from parkour.runtime import atomic_json

class MotionDiagnostics:
    def __init__(self,env,done):
        self.env,self.done=env,done
        self.samples=[]
        self.nonfoot_ids=[i for i in range(env.contacts.data.net_forces_w.shape[1]) if i not in env.contact_ids]
        self.original_update=env.scene.update
        self.elapsed=0.
        def update(dt):
            self.original_update(dt)
            self.elapsed+=dt
            self.capture()
        env.scene.update=update

    def capture(self):
        e=self.env
        def cpu(x):return x.detach().cpu().numpy().copy()
        active=e.order[e.stage.clamp_max(e.seq.get('sequence_length',4)-1)]
        self.samples.append({
            'time':self.elapsed,'valid':cpu(~self.done),
            'root_z':cpu(e.robot.data.root_pos_w[:,2]-e.scene.env_origins[:,2]),
            'root_vz':cpu(e.robot.data.root_lin_vel_w[:,2]),
            'foot_pos':cpu(e.robot.data.body_pos_w[:,e.foot_ids]-e.scene.env_origins[:,None,:]),
            'foot_vel':cpu(e.robot.data.body_lin_vel_w[:,e.foot_ids]),
            'force':cpu(e.contacts.data.net_forces_w[:,e.contact_ids]),
            'nonfoot_peak':cpu(e.contacts.data.net_forces_w[:,self.nonfoot_ids].norm(dim=-1).amax(dim=1)),
            'action':cpu(e.actions),'torque':cpu(e.robot.data.applied_torque),
            'active':cpu(active),'stage':cpu(e.stage),'phase':cpu(e.phase)})

    def close(self,out,scenario_ids):
        self.env.scene.update=self.original_update
        arrays={k:np.stack([s[k] for s in self.samples]) for k in self.samples[0]}
        np.savez_compressed(out/'motion-trace.npz',**arrays)
        report=summarize(arrays,self.env.physics_dt,scenario_ids,self.env.foot_names)
        atomic_json(out/'diagnostics.json',report)
        return report

def summarize(a,dt,scenario_ids,foot_names):
    results=[]
    for i,sid in enumerate(scenario_ids):
        valid=a['valid'][:,i].astype(bool)
        force=a['force'][valid,i];z=a['root_z'][valid,i];vz=a['root_vz'][valid,i]
        pos=a['foot_pos'][valid,i];vel=a['foot_vel'][valid,i]
        normal=np.maximum(force[:,:,2],0)
        # Separate diagnostic hysteresis sampled at physics rate; doesn't modify policy observation.
        contact=np.zeros_like(normal,dtype=bool); state=np.zeros(4,dtype=bool)
        for t in range(len(normal)):
            state=np.where(state,normal[t]>2,normal[t]>5);contact[t]=state
        count=contact.sum(axis=1);flight=count==0
        def max_duration(mask):
            longest=streak=0
            for x in mask:streak=streak+1 if x else 0;longest=max(longest,streak)
            return longest*dt
        active=a['active'][valid,i];other=np.arange(4)[None,:]!=active[:,None]
        # Motion only across consecutive supported samples; excludes swing displacement.
        supported=contact[1:]&contact[:-1]&other[1:]&other[:-1]
        travel=np.linalg.norm(np.diff(pos[:,:,:2],axis=0),axis=-1)
        peaks=[]
        for foot in range(4):
            onsets=np.flatnonzero(contact[1:,foot]&~contact[:-1,foot])+1
            for start in onsets:
                end=min(len(normal),start+int(round(.05/dt)))
                peaks.append(float(normal[start:end,foot].sum()*dt))
        rows={'scenario_id':sid,'duration_s':len(z)*dt,'root_z_range_m':float(np.ptp(z)),
            'root_vz_abs_max_m_s':float(np.max(np.abs(vz))),
            'all_feet_air_time_s':float(flight.sum()*dt),'max_all_feet_air_duration_s':max_duration(flight),
            'has_flight_20ms':bool(max_duration(flight)>=.02-1e-8),
            'under_three_contacts_fraction':float((count<3).mean()),
            'nonfoot_contact_fraction':float((a['nonfoot_peak'][valid,i]>5).mean()),
            'nonfoot_force_peak_N':float(a['nonfoot_peak'][valid,i].max()),
            'foot_normal_force_peak_N':float(normal.max()),
            'landing_50ms_impulse_max_Ns':max(peaks,default=0.),
            'support_travel_total_m':float((travel*supported).sum()),
            'supported_speed_peak_m_s':float(np.max(np.linalg.norm(vel[:,:,:2],axis=-1)*contact*other)),
            'torque_abs_peak_Nm':float(np.abs(a['torque'][valid,i]).max()),
            'action_clip_fraction':float((np.abs(a['action'][valid,i])>=.999).mean())}
        results.append(rows)
    keys=[k for k,v in results[0].items() if isinstance(v,(float,int)) and not isinstance(v,bool)]
    return {'schema_version':2,'physics_hz':1/dt,'foot_names':foot_names,'episodes':len(results),
        'flight_episode_count':sum(r['has_flight_20ms'] for r in results),
        'means':{k:float(np.mean([r[k] for r in results])) for k in keys},
        'maxima':{k:float(np.max([r[k] for r in results])) for k in keys},
        'definitions':{'flight':'No feet above 5N onset / 2N release hysteresis; continuous >=20ms. Does not exclude non-foot support.',
            'landing_50ms_impulse':'Integral of normal foot force for 50ms after contact onset; includes weight support; end-of-episode windows truncated.',
            'support_travel':'XY path length summed over non-active feet supported at both adjacent physics samples; foot-center motion, not proven slip.',
            'scope':'All first episodes, includes initial settling, ends before auto-reset. Oracle simulated net contact forces, not physical sensor readings.'},
        'results':results}
