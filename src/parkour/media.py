"""Original-frame recordings of a visible grid; hidden robots still simulate."""
from __future__ import annotations
import numpy as np
import torch
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
import isaaclab.sim as sim_utils
from pxr import UsdGeom
import imageio.v2 as imageio
from parkour.runtime import atomic_json


class ParallelRecorder:
    def __init__(self, env, out, name='evaluation', count=16, camera_side=None):
        self.env, self.out, self.name = env, out, name
        origins=env.scene.env_origins.cpu().numpy()
        side=int(np.ceil(np.sqrt(min(count,env.num_envs))))
        xs=sorted(set(origins[:,0]),reverse=True)[:side]
        ys=sorted(set(origins[:,1]))[:side]
        self.ids=[i for i,o in enumerate(origins) if o[0] in xs and o[1] in ys][:count]
        if not self.ids:self.ids=[0]
        selected=set(self.ids)
        for index,path in enumerate(env.scene.env_prim_paths):
            if index not in selected:
                UsdGeom.Imageable(env.scene.stage.GetPrimAtPath(path)).MakeInvisible()
        env.render_mode='rgb_array'
        env.cfg.viewer.resolution=(1280,720)
        center=origins[self.ids].mean(axis=0)+np.array([0,0,.25])
        camera_side = side if camera_side is None else camera_side
        if not isinstance(camera_side, int) or camera_side < 1:
            raise ValueError("Camera side must be a positive integer")
        distance=max(2.0,float(camera_side)*2.3)
        self.camera_metadata={"framing_side": camera_side, "enabled_grid_side": side,
            "look_at_m": center.tolist(), "eye_m": (center+np.array([distance,-distance,distance*1.3])).tolist(),
            "note": "visible_env_ids are render-enabled IDs; camera frustum may exclude some robots"}
        env.sim.set_camera_view(center+np.array([distance,-distance,distance*1.3]),center)
        config=VisualizationMarkersCfg(prim_path='/World/VideoTargets',markers={
            'support':sim_utils.SphereCfg(radius=.025,visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(.9,.2,.15))),
            'active':sim_utils.SphereCfg(radius=.035,visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.,.8,.05)))})
        self.markers=VisualizationMarkers(config)
        self.markers.visualize(translations=env.targets[self.ids].reshape(-1,3))
        for _ in range(40):env.render()
        self.writer=imageio.get_writer(str(out/(name+'.mp4')),fps=25,codec='libx264')
        self.frames=0
        self.trace=[]

    def capture(self, step, finished=None, iteration=None):
        if step%2:return
        env=self.env
        indices=torch.zeros(len(self.ids),4,device=env.device,dtype=torch.long)
        if getattr(env,'contact_group_all',False):
            indices[:]=1
        elif hasattr(env,'stage'):
            active=env.active_feet()[self.ids]
            indices[torch.arange(len(self.ids),device=env.device),active]=1
        self.markers.visualize(translations=env.targets[self.ids].reshape(-1,3),marker_indices=indices.flatten())
        frame=env.render()
        if self.frames==0:
            if frame.max()==0:raise RuntimeError('Black renderer output')
            imageio.imwrite(self.out/('first-frame.png' if self.name=='evaluation' else self.name+'-preview.png'),frame)
        self.writer.append_data(frame)
        row={'sim_time_s':step*env.step_dt,'visible_env_ids':self.ids,
             'root_state_w':env.robot.data.root_state_w[self.ids].tolist(),
             'foot_positions_w':env.robot.data.body_pos_w[self.ids][:,env.foot_ids].tolist(),
             'targets_w':env.targets[self.ids].tolist(),
             'foot_normal_force_N':env.contacts.data.net_forces_w[self.ids][:,env.contact_ids,2].tolist(),
             'contact_state':env.contact_on[self.ids].tolist(),
             'root_vz':env.robot.data.root_lin_vel_w[self.ids,2].tolist(),
             'actions':env.actions[self.ids].tolist()}
        if finished is not None:row['first_episode_finished']=finished[self.ids].tolist()
        if iteration is not None:row['learning_iteration']=iteration
        if hasattr(env,'stage'):
            row.update(stage=env.stage[self.ids].tolist(),phase=env.phase[self.ids].tolist())
        self.trace.append(row)
        self.frames+=1

    def close(self, **metadata):
        self.writer.close()
        self.writer=None
        payload={'artifact_type':'original_simulation_frames','layout':'parallel',
                 'visible_env_ids':self.ids,'total_simulated_envs':self.env.num_envs,
                 'fps':25,'frame_count':self.frames,'video_start_sim_time_s':0.,'frame_dt_s':.04,
                 'resolution':[1280,720],'camera':self.camera_metadata,'trace':self.trace,**metadata}
        if hasattr(self.env,'phase_labels'):
            payload['phase_labels']=self.env.phase_labels
            payload['contact_group']='all_four'
        atomic_json(self.out/('replay.json' if self.name=='evaluation' else self.name+'-replay.json'),payload)
        return payload


class FollowRecorder:
    """One original first episode, third-person camera following body yaw."""
    def __init__(self,env,out,name='evaluation',env_index=0):
        import math
        if not 0<=env_index<env.num_envs:raise ValueError('Invalid followed environment')
        self.env,self.out,self.name=env,out,name;self.ids=[env_index];self.frames=0;self.trace=[]
        for i,path in enumerate(env.scene.env_prim_paths):
            if i!=env_index:UsdGeom.Imageable(env.scene.stage.GetPrimAtPath(path)).MakeInvisible()
        # Nonzero clones inherit env0 visibility unless explicitly overridden.
        UsdGeom.Imageable(env.scene.stage.GetPrimAtPath(env.scene.env_prim_paths[env_index])).MakeVisible()
        followed=UsdGeom.Imageable(env.scene.stage.GetPrimAtPath(env.scene.env_prim_paths[env_index]+'/Robot'))
        if followed.ComputeVisibility()==UsdGeom.Tokens.invisible:raise RuntimeError('Followed robot is invisible')
        env.render_mode='rgb_array';env.cfg.viewer.resolution=(1280,720)
        self.plan_markers=None
        if hasattr(env,'plan'):
            self.plan_markers=VisualizationMarkers(VisualizationMarkersCfg(prim_path='/World/FollowPlannedContacts',markers={
                'planned':sim_utils.SphereCfg(radius=.035,visual_material=sim_utils.PreviewSurfaceCfg(diffuse_color=(1.,0.,0.),emissive_color=(.45,0.,0.)))}))
        self.eye=None;self.look=None;self.yaw=None
        self._camera()
        for _ in range(40):env.render()
        self.writer=imageio.get_writer(str(out/(name+'.mp4')),fps=25,codec='libx264')
    def _camera(self):
        import math
        root=self.env.robot.data.root_state_w[self.ids[0]].detach().cpu().numpy()
        w,x,y,z=root[3:7];yaw=math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))
        if self.yaw is None:self.yaw=yaw
        else:self.yaw+=.16*math.atan2(math.sin(yaw-self.yaw),math.cos(yaw-self.yaw))
        forward=np.array([math.cos(self.yaw),math.sin(self.yaw),0.]);right=np.array([math.sin(self.yaw),-math.cos(self.yaw),0.])
        desired_eye=root[:3]-2.5*forward+.85*right+np.array([0,0,1.4])
        desired_look=root[:3]+.5*forward+np.array([0,0,.08])
        self.eye=desired_eye if self.eye is None else .2*desired_eye+.8*self.eye
        self.look=desired_look if self.look is None else .2*desired_look+.8*self.look
        self.env.sim.set_camera_view(self.eye,self.look)
    def capture(self,step,finished=None,iteration=None):
        if step%2:return
        if finished is not None and bool(finished[self.ids[0]]):return
        displayed=None
        if self.plan_markers is not None:
            from parkour.planned_contacts import planned_contacts
            override=getattr(self.env,'follow_planned_contacts_override',None)
            if override is None:
                points,normals,indices,valid=planned_contacts(self.env,self.ids[0])
                displayed={'positions_w':points.cpu().tolist(),'normals_w':normals.cpu().tolist(),'surface_indices':indices.cpu().tolist(),'valid':valid.cpu().tolist(),'horizon':4}
            else:
                displayed=override
                points=torch.tensor(displayed['positions_w'],device=self.env.device)
                normals=torch.tensor(displayed['normals_w'],device=self.env.device)
            self.plan_markers.visualize(translations=points+.025*normals)
        self._camera();frame=self.env.render()
        if self.frames==0:
            if frame.max()==0:raise RuntimeError('Black follow-camera output')
            imageio.imwrite(self.out/('first-frame.png' if self.name=='evaluation' else self.name+'-preview.png'),frame)
        self.writer.append_data(frame);self.frames+=1
        i=self.ids[0]
        env=self.env
        row={'sim_time_s':step*env.step_dt,'env_index':i,
            'root_state_w':env.robot.data.root_state_w[i].tolist(),'eye_m':self.eye.tolist(),'look_at_m':self.look.tolist(),
            'foot_positions_w':env.robot.data.body_pos_w[i,env.foot_ids].tolist(),
            'targets_w':env.targets[i].tolist(),'foot_normal_force_N':env.contacts.data.net_forces_w[i,env.contact_ids,2].tolist(),
            'contact_state':env.contact_on[i].tolist(),'root_vz':float(env.robot.data.root_lin_vel_w[i,2]),
            'actions':env.actions[i].tolist()}
        if hasattr(env,'progress'):
            row.update(target_indices=env.progress.target[i].tolist(),accepted_indices=env.progress.accepted[i].tolist(),
                       measured_jump_count=int(env.flights.count[i]))
        if displayed is not None:row['planned_contacts']=displayed
        self.trace.append(row)
    def close(self,**metadata):
        self.writer.close();self.writer=None
        payload={'artifact_type':'original_simulation_frames','layout':'third_person_follow','visible_env_ids':self.ids,
            'total_simulated_envs':self.env.num_envs,'fps':25,'frame_count':self.frames,'frame_dt_s':.04,
            'video_start_sim_time_s':0.,'resolution':[1280,720],'trace':self.trace,
            'camera':{'mode':'smoothed_body_yaw_third_person','behind_m':2.5,'side_m':.85,'above_body_m':1.4},
            'planned_contact_overlay':{'color':'red','horizon':4,'meaning':'Active planned targets, not measured landings','radius_m':.035,'normal_display_offset_m':.025} if self.plan_markers is not None else None,
            'scope':'Single first episode; no padding or stitching after failure/reset',**metadata}
        atomic_json(self.out/('replay.json' if self.name=='evaluation' else self.name+'-replay.json'),payload)
        return payload
