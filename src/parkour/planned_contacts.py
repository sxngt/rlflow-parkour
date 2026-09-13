"""The active plan's next four pair-contact targets; no future outcome labels."""
import torch
from parkour.candidate_plan import gather_plan

def planned_contacts(env,index=0,horizon=4):
 if horizon not in (3,4):raise ValueError('Display horizon must be three or four')
 plan=getattr(env,'candidate_plan',env.plan)
 n=env.plan.shape[1]
 indices=env.progress.target[index,:,None]+torch.arange(horizon,device=env.device)[None,:]
 valid=indices<n;indices=indices.clamp_max(n-1)
 batch=indices[None].expand(env.num_envs,-1,-1)
 points=gather_plan(plan,batch)[index]+env.scene.env_origins[index]
 # Pair, horizon, left/right, xyz. Mask instead of repeating the final dots.
 positions=points[valid].reshape(-1,3)
 normals=env.surface_normals[indices][valid].repeat_interleave(2,dim=0)
 return positions,normals,indices,valid
