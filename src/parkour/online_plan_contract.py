"""Admission rules for a scheduled asynchronous foothold update."""
import math


def admission(proposal,pending,step,root,target,articulation=None):
    if proposal.get('id')!=pending['id'] or proposal.get('activation_step')!=pending['activation_step']:
        return 'response_identity_mismatch',None
    if not proposal.get('accepted'):return proposal.get('rejection','planner_rejected'),None
    if step!=pending['activation_step']:return 'deadline_missed',None
    predicted=proposal.get('predicted_root',[])
    if len(predicted)!=3 or len(root)!=3 or not all(math.isfinite(x) for x in [*root,*predicted]):return 'invalid_predicted_state',None
    error=math.sqrt(sum((a-b)**2 for a,b in zip(root,predicted)))
    if error>.08 or target!=proposal.get('predicted_target') or max(target)>=proposal.get('start_surface',-1):return 'stale_state_or_contact',error
    if 'predicted_quaternion' in proposal:
        if articulation is None:return 'missing_articulation_state',error
        for key,n in [('quaternion',4),('joint_position',12),('velocity',3)]:
            predicted=proposal.get('predicted_'+key,[]);actual=articulation.get(key,[])
            if len(predicted)!=n or len(actual)!=n or not all(math.isfinite(v) for v in predicted+actual):return 'invalid_articulation_state',error
        q=proposal['predicted_quaternion'];actual=articulation['quaternion']
        denom=math.sqrt(sum(v*v for v in q)*sum(v*v for v in actual))
        if denom<1e-8:return 'invalid_articulation_state',error
        angle=2*math.acos(min(1.,abs(sum(a*b for a,b in zip(q,actual)))/denom))
        if angle>.15:return 'stale_orientation',error
        if max(abs(a-b) for a,b in zip(proposal['predicted_joint_position'],articulation['joint_position']))>.15:return 'stale_joint_state',error
        if math.sqrt(sum((a-b)**2 for a,b in zip(proposal['predicted_velocity'],articulation['velocity'])))>.5:return 'stale_velocity',error
    return None,error
