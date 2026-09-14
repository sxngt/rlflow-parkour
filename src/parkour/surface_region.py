"""Exposed shared-surface contact regions; independent of target point radius."""
import torch

def exposed_projection(foot,indices,rotations,top_centers,box_centers,box_sizes):
    """Reject selected-plane projections buried in another oriented cuboid.

    Inputs are course-local. Contact force and foot margin are checked separately.
    This is geometric attribution, not a simulator contact-pair sensor.
    """
    normals=rotations[indices][...,2]
    height=((foot-top_centers[indices])*normals).sum(-1,keepdim=True)
    point=foot-height*normals
    delta=point[:,:,None,:]-box_centers[None,None,:,:]
    local=torch.einsum('kji,nfkj->nfki',rotations,delta)
    buried=(local.abs()<=box_sizes[None,None,:,:]/2+1e-6).all(-1)
    others=torch.arange(len(box_centers),device=foot.device)[None,None,:]!=indices[:,:,None]
    return ~(buried&others).any(-1)


def exposed_projection_batched(foot,indices,rotations,top_centers,box_centers,box_sizes):
    """Per-environment surface tables: rotations [N,S,3,3], centers [N,S,3], box sizes [N,S,3]; foot [N,4,3]; indices [N,4]."""
    n=foot.shape[0];env=torch.arange(n,device=foot.device)[:,None]
    R=rotations[env,indices];normals=R[...,2]
    height=((foot-top_centers[env,indices])*normals).sum(-1,keepdim=True)
    point=foot-height*normals
    delta=point[:,:,None,:]-box_centers[:,None,:,:]
    local=torch.einsum('nkji,nfkj->nfki',rotations,delta)
    buried=(local.abs()<=box_sizes[:,None,:,:]/2+1e-6).all(-1)
    others=torch.arange(box_centers.shape[1],device=foot.device)[None,None,:]!=indices[:,:,None]
    return ~(buried&others).any(-1)
