"""Map-specific foothold checks, distinct from minimum trunk flight distance."""
import torch


def mapped_contact_gate_reference(env):
    goal=env.targets[:,:,:2]-env.scene.env_origins[:,None,:2]
    feet=env.robot.data.body_pos_w[:,env.foot_ids]-env.scene.env_origins[:,None,:]
    valid=torch.ones(env.num_envs,dtype=torch.bool,device=env.device)
    for foot,name in enumerate(env.foot_names):
        first=env.first_touch.positions[:,foot]
        matches=torch.zeros(env.num_envs,dtype=torch.int64,device=env.device)
        supported=torch.zeros_like(valid)
        for surface in env.cfg.support_contract['layout']['surfaces']:
            if surface['foot']!=name and not (env.cfg.support_contract['layout'].get('mode')=='full-gap' and surface['foot']=='all'):continue
            x0,x1,y0,y1=surface['bounds_xy_m'];z=surface['top_z_m']
            selected=(goal[:,foot,0]>=x0+.02-1e-6)&(goal[:,foot,0]<=x1-.02+1e-6)&(goal[:,foot,1]>=y0+.02-1e-6)&(goal[:,foot,1]<=y1-.02+1e-6)
            def inside(p):return (p[:,0]>=x0)&(p[:,0]<=x1)&(p[:,1]>=y0)&(p[:,1]<=y1)
            on_top=(feet[:,foot,2]>=z)&(feet[:,foot,2]<=z+.04)
            matches+=selected.long()
            supported|=selected&inside(first)&inside(feet[:,foot,:2])&on_top
        valid&=(matches==1)&supported&env.first_touch.seen[:,foot]
    normal=env.contacts.data.net_forces_w[:,env.contact_ids,2]
    return valid&(normal>2).all(dim=1)


def mapped_contact_gate_vectorized(env):
    """Equivalent checks with precomputed immutable-map comparison bounds."""
    layout=env.cfg.support_contract['layout']
    feet=env.robot.data.body_pos_w[:,env.foot_ids]-env.scene.env_origins[:,None,:]
    key=(id(layout),tuple(env.foot_names),feet.dtype,str(feet.device))
    cache=getattr(env,'_mapped_contact_bounds_cache',None)
    if cache is None or cache[0]!=key:
        groups=[[surface for surface in layout['surfaces'] if surface['foot']==name or (layout.get('mode')=='full-gap' and surface['foot']=='all')] for name in env.foot_names]
        size=max(1,max(map(len,groups)))
        bounds=[];limits=[];heights=[];present=[]
        for group in groups:
            b=[];l=[];h=[];m=[]
            for surface in group:
                x0,x1,y0,y1=surface['bounds_xy_m'];z=surface['top_z_m']
                b.append([x0,x1,y0,y1])
                # Python arithmetic matches the reference scalar rounding exactly.
                l.append([x0+.02-1e-6,x1-.02+1e-6,y0+.02-1e-6,y1-.02+1e-6])
                h.append([z,z+.04]);m.append(True)
            b += [[0.,0.,0.,0.]]*(size-len(b));l += [[0.,0.,0.,0.]]*(size-len(l))
            h += [[0.,0.]]*(size-len(h));m += [False]*(size-len(m))
            bounds.append(b);limits.append(l);heights.append(h);present.append(m)
        tensors=[torch.tensor(values,device=feet.device,dtype=feet.dtype) for values in (bounds,limits,heights)]
        mask=torch.tensor(present,device=feet.device,dtype=torch.bool)
        cache=(key,*tensors,mask);env._mapped_contact_bounds_cache=cache
        env._mapped_contact_bounds_source=layout
    _,bounds,limits,heights,present=cache
    goal=(env.targets[:,:,:2]-env.scene.env_origins[:,None,:2])[:,:,None,:]
    first=env.first_touch.positions[:,:,None,:]
    current=feet[:,:,None,:]
    def inside(points,rectangle):
        return ((points[...,0]>=rectangle[None,...,0])&(points[...,0]<=rectangle[None,...,1])&
                (points[...,1]>=rectangle[None,...,2])&(points[...,1]<=rectangle[None,...,3]))
    selected=inside(goal,limits)&present[None,:,:]
    supported=selected&inside(first,bounds)&inside(current,bounds)&(
        current[...,2]>=heights[None,...,0])&(current[...,2]<=heights[None,...,1])
    valid=((selected.sum(dim=2)==1)&supported.any(dim=2)&env.first_touch.seen).all(dim=1)
    return valid&(env.contacts.data.net_forces_w[:,env.contact_ids,2]>2).all(dim=1)


def mapped_contact_gate(env):
    # Keep the running research contract on its reference path until benchmarked.
    if getattr(env,'vectorized_map_contact',False):
        return mapped_contact_gate_vectorized(env)
    return mapped_contact_gate_reference(env)
