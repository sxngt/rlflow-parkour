"""Map-specific foothold checks, distinct from minimum trunk flight distance."""
import torch


def mapped_contact_gate(env):
    goal=env.targets[:,:,:2]-env.scene.env_origins[:,None,:2]
    feet=env.robot.data.body_pos_w[:,env.foot_ids]-env.scene.env_origins[:,None,:]
    valid=torch.ones(env.num_envs,dtype=torch.bool,device=env.device)
    for foot,name in enumerate(env.foot_names):
        first=env.first_touch.positions[:,foot]
        matches=torch.zeros(env.num_envs,dtype=torch.int64,device=env.device)
        supported=torch.zeros_like(valid)
        for surface in env.cfg.support_contract['layout']['surfaces']:
            if surface['foot']!=name:continue
            x0,x1,y0,y1=surface['bounds_xy_m'];z=surface['top_z_m']
            selected=(goal[:,foot,0]>=x0+.02-1e-6)&(goal[:,foot,0]<=x1-.02+1e-6)&(goal[:,foot,1]>=y0+.02-1e-6)&(goal[:,foot,1]<=y1-.02+1e-6)
            def inside(p):return (p[:,0]>=x0)&(p[:,0]<=x1)&(p[:,1]>=y0)&(p[:,1]<=y1)
            on_top=(feet[:,foot,2]>=z)&(feet[:,foot,2]<=z+.04)
            matches+=selected.long()
            supported|=selected&inside(first)&inside(feet[:,foot,:2])&on_top
        valid&=(matches==1)&supported&env.first_touch.seen[:,foot]
    normal=env.contacts.data.net_forces_w[:,env.contact_ids,2]
    return valid&(normal>2).all(dim=1)
