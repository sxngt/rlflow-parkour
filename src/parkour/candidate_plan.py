"""Per-environment foothold candidates for matched-Tracker physical rollouts."""
import torch


def gather_plan(plan,indices):
    n,_,h=indices.shape
    pairs=torch.arange(2,device=indices.device)[None,:,None].expand(n,2,h)
    if plan.ndim==4:return plan[pairs,indices]
    if plan.ndim!=5 or plan.shape[0]!=n:raise ValueError('Invalid candidate plan dimensions')
    envs=torch.arange(n,device=indices.device)[:,None,None]
    return plan[envs,pairs,indices]


def install_candidates(env,start_surface=1):
    if env.num_envs%9:raise ValueError('Use equal replication: environment count divisible by nine')
    if start_surface<1 or env.plan.shape[1]<start_surface+5:raise ValueError('Need four intermediate surfaces and an unchanged terminal stance')
    offsets=[(x,y) for x in (-.08,0.,.08) for y in (-.04,0.,.04)]
    env.candidate_plan=env.plan[None].repeat(env.num_envs,1,1,1,1)
    ids=torch.arange(env.num_envs,device=env.device)%9
    for surface in range(start_surface,start_surface+4):
        local=torch.tensor([[*offsets[int(i)],0.] for i in ids.cpu()],device=env.device)
        world=local@env.surface_rotations[surface].T
        env.candidate_plan[:,:,surface]+=world[:,None,None,:]
        # Geometry gate for every shifted foot center on the selected surface.
        relative=env.candidate_plan[:,:,surface]-env.surface_centers[surface]
        uv=relative@env.surface_rotations[surface]
        if not bool((uv[...,:2].abs()<=env.surface_halves[surface]).all()):raise ValueError('Candidate violates surface margin')
    return {'contract':'four_step_candidate_rollout_v1','horizon':4,'start_surface':start_surface,'offsets_surface_xy_m':offsets,
        'candidate_id_by_environment':ids.cpu().tolist(),'replicates_per_candidate':env.num_envs//9,
        'scope':'Nine target-offset sequences starting at start_surface; same checkpoint. Physical policy rollouts; replay validation is recorded separately when branching after a prefix. No real-time planning claim.'}
