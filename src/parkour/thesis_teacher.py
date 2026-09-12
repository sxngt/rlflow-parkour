"""Read-only adapter for the user's own master-thesis A1 velocity policy.

No claim of foothold tracking, turning-command support, or identical old physics.
Source network implementation is imported from the recorded local repository.
"""
import importlib.util
from pathlib import Path
import torch,yaml
from parkour.runtime import sha256

class ThesisVelocityTeacher:
    def __init__(self,env,checkpoint,source_root,speed=.5):
        self.env=env;path=Path(checkpoint).resolve();root=Path(source_root).resolve()
        config_path=path.parent.parent/'config.yaml'
        cfg=yaml.safe_load(config_path.read_text())
        if cfg['robot']['name']!='a1' or cfg['algorithm']['name']!='ppo':raise ValueError('A1 PPO teacher required')
        if cfg['sim']['dt']*cfg['sim']['control_decimation']!=env.step_dt:raise ValueError('Teacher control period differs')
        network_path=root/'src/quadruped_rl/algorithms/networks.py'
        spec=importlib.util.spec_from_file_location('parkour_user_thesis_network',network_path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.actor=module.GaussianActor(48,12,cfg['algorithm']['network']['actor']).to(env.device)
        state=torch.load(path,map_location=env.device,weights_only=True)
        self.actor.load_state_dict(state['actor']);self.actor.eval()
        self.action_scale=cfg['sim']['action_scale'];self.speed=speed
        if not 0<speed<=1.:raise ValueError('Probe speed must be in (0,1]')
        self.clipped=0;self.total=0
        self.metadata={'checkpoint':str(path),'checkpoint_sha256':sha256(path),'config':str(config_path),'config_sha256':sha256(config_path),
            'network_source':str(network_path),'network_source_sha256':sha256(network_path),'training_seed':cfg['run']['seed'],
            'source_project':'master-thesis','command_forward_m_s':speed,'source_action_scale':self.action_scale,
            'target_action_scale':env.cfg.action_scale,'policy_parameter_count':sum(p.numel() for p in self.actor.parameters()),
            'observation_contract':'48: linvel*2,angvel*.25,gravity,body command*2,joint delta,jointvel*.05,previous action in source units',
            'scope':'Frozen existing velocity policy; no foothold or heading feedback, no parkour fine-tuning; current contact/actuator/terrain contracts apply'}
    @torch.inference_mode()
    def act(self):
        e=self.env;d=e.robot.data
        cmd=torch.zeros(e.num_envs,3,device=e.device);cmd[:,0]=self.speed
        prior=e.actions*e.cfg.action_scale/self.action_scale
        obs=torch.cat([d.root_lin_vel_b*2,d.root_ang_vel_b*.25,d.projected_gravity_b,cmd*2,
            d.joint_pos-d.default_joint_pos,d.joint_vel*.05,prior],dim=1)
        action=self.actor.body(obs)*self.action_scale/e.cfg.action_scale
        if not torch.isfinite(action).all():raise ValueError('Nonfinite teacher action')
        self.clipped+=int((action.abs()>1).sum());self.total+=action.numel()
        return action
