"""Evaluation-only bundle: travel policy followed by a validated stance policy."""
import torch

def handoff_eligible(accepted,last,root,goal,velocity,gravity,support_count,done):
    return (accepted==last).all(1)&((root[:,:2]-goal[:2]).norm(dim=1)<.3)&(velocity.norm(dim=1)<1.)&(gravity[:,2]<-.8660254)&(support_count>=2)&~done

class TerminalPolicy:
    def __init__(self,path,config,env):
        from parkour.learning import read_checkpoint,make_algorithm,restore
        from parkour.runtime import sha256
        data=read_checkpoint(path);other=data['config']
        if config.get('task')!='a1_continuous_tracker_v1' or other.get('task')!=config['task']:
            raise ValueError('Terminal bundle requires continuous Tracker policies')
        for key,default in [('action_limit',1.),('pair_contact_quorum','both'),('initial_rear_target','own_stance'),('observation_history',None)]:
            if config.get(key,default)!=other.get(key,default):raise ValueError('Terminal policy contract differs: '+key)
        for key in ('foot_names','calibration'):
            if config['terrain_contract'][key]!=other['terrain_contract'][key]:raise ValueError('Terminal robot/calibration differs')
        if env.cfg.observation_space!=105:raise ValueError('Terminal bundle expects105observations')
        with torch.random.fork_rng(devices=[] if str(env.device)=='cpu' else [0]):
            self.alg,self.norm=make_algorithm(other,env)
            restore(data,other,self.alg,self.norm,env,training=False)
        self.alg.policy.eval();self.norm.eval()
        self.env=env;self.latched=torch.zeros(env.num_envs,dtype=torch.bool,device=env.device)
        self.steps=torch.full((env.num_envs,),-1,dtype=torch.long,device=env.device)
        self.metadata={'contract':'terminal_policy_handoff_v1','checkpoint':{'path':str(path.resolve()),'sha256':sha256(path)},
            'gate':'both pair accepted final surface; at least2currently valid foot supports; rootXY within0.3m of goal; body speed<1m/s; tilt<30deg; latch until episode ends',
            'scope':'Two fixed RL policies with independent normalization; not a single-checkpoint result; no training updates'}
    def apply(self,raw,action,step,done):
        e=self.env
        eligible=handoff_eligible(e.progress.accepted,e.progress.target_count-1,e.robot.data.root_pos_w-e.scene.env_origins,e.goal,e.robot.data.root_lin_vel_w,e.robot.data.projected_gravity_b,e.current_valid.sum(1),done)
        new=eligible&~self.latched;self.steps[new]=step;self.latched|=eligible
        active=self.latched&~done
        if active.any():
            action=action.clone();action[active]=self.alg.policy.act_inference(self.norm(raw[active]))
        return action
