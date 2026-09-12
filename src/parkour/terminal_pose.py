"""Explicit evaluation-only terminal pose hold; not a learned tracker result."""
import torch

class TerminalPoseHold:
    def __init__(self,env,mode='settled'):
        if mode not in ('settled','contact-capture'):raise ValueError('Unknown terminal pose mode')
        self.hold_steps=3 if mode=='settled' else 1
        self.angular_limit=2. if mode=='settled' else 8.
        self.env=env
        self.latched=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
        self.steps=torch.full((env.num_envs,),-1,dtype=torch.long,device=env.device)
        self.hold=torch.zeros_like(self.steps)
        self.target=((env.calibrated_joint_pos-env.robot.data.default_joint_pos[0])/env.cfg.action_scale)
        if not torch.isfinite(self.target).all() or (self.target.abs()>env.cfg.action_limit).any():
            raise ValueError('Calibrated stance outside action contract')
        self.metadata={'contract':('settled_terminal_pose_hold_v1' if mode=='settled' else 'contact_capture_terminal_pose_hold_v1'),'gate_hold_steps':self.hold_steps,'blend_steps':15,
            'target_joint_positions':env.calibrated_joint_pos.tolist(),
            'gate':f'Both pair final contacts accepted; >=3 valid supports; rootXY error<0.12m; linear speed<0.3m/s; angular speed<{self.angular_limit}rad/s; tilt<15deg; {self.hold_steps} consecutive control steps',
            'scope':'Fixed RL travel policy plus explicit calibrated joint-pose hold through existing PD actuators; not pure RL terminal stabilization; normal success/failure criteria retained'}

    def apply(self,raw,action,step,done):
        e=self.env;root=e.robot.data.root_pos_w-e.scene.env_origins
        ready=(e.progress.accepted==e.progress.target_count-1).all(1)&((root[:,:2]-e.goal[:2]).norm(dim=1)<.12)
        ready&=(e.current_valid.sum(1)>=3)&(e.robot.data.root_lin_vel_w.norm(dim=1)<.3)
        ready&=(e.robot.data.root_ang_vel_b.norm(dim=1)<self.angular_limit)&(e.robot.data.projected_gravity_b[:,2]<-.9659258)&~done
        self.hold=torch.where(ready,self.hold+1,0)
        new=(self.hold>=self.hold_steps)&~self.latched;self.steps[new]=step;self.latched|=new
        active=self.latched&~done
        alpha=((step-self.steps+1)/15.).clamp(0,1)
        mixed=(1-alpha[:,None])*action.clamp(-e.cfg.action_limit,e.cfg.action_limit)+alpha[:,None]*self.target
        return torch.where(active[:,None],mixed,action)
