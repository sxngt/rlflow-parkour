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
