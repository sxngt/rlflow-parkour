"""Admission rules for a scheduled asynchronous foothold update."""
import math


def admission(proposal,pending,step,root,target):
    if proposal.get('id')!=pending['id'] or proposal.get('activation_step')!=pending['activation_step']:
        return 'response_identity_mismatch',None
    if not proposal.get('accepted'):return proposal.get('rejection','planner_rejected'),None
    if step!=pending['activation_step']:return 'deadline_missed',None
    predicted=proposal.get('predicted_root',[])
    if len(predicted)!=3 or len(root)!=3 or not all(math.isfinite(x) for x in [*root,*predicted]):return 'invalid_predicted_state',None
    error=math.sqrt(sum((a-b)**2 for a,b in zip(root,predicted)))
    if error>.08 or target!=proposal.get('predicted_target') or max(target)>=proposal.get('start_surface',-1):return 'stale_state_or_contact',error
    return None,error
