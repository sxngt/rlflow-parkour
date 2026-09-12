"""Read-only successful-landing snapshots for later replay validation.

These are articulated state records, not complete simulator checkpoints: solver
warm-start and hidden actuator state are not claimed to be reproducible.
"""
import numpy as np
from parkour.runtime import atomic_json


def capture_transition(env, before, ids):
    if not getattr(env, 'capture_transition_states', False):
        return
    if not hasattr(env, 'transition_state_records'):
        env.transition_state_records = []
    observation = env._get_observations()['policy']
    for i in ids.tolist():
        if bool(env.evaluation_done[i]):
            continue
        def cpu(t):
            return t[i].detach().cpu().numpy().copy()
        state = {key:cpu(value) for key,value in before.items()}
        # World translations depend on parallel-environment layout; store local.
        state['root'][:3] -= state['origins']
        state['target_local'] = cpu(env.targets) - state['origins'][None,:]
        state['post_transition_observation'] = cpu(observation)
        state['launch_origin_xy'] = cpu(env.chain.launch_origin)
        state['completed_hops'] = cpu(env.chain.completed)
        state['required_apex'] = cpu(env.required_apex)
        state['env_index'] = np.asarray(i,dtype=np.int64)
        env.transition_state_records.append(state)


def save_transition_states(env, out, scenario_ids):
    records = getattr(env,'transition_state_records',[])
    if not records:
        atomic_json(out/'transition-states.json',{'schema_version':1,'count':0,'records':[],
                    'scope':'No successful landing transition in first episodes'})
        return
    keys=set(records[0])
    if any(set(r)!=keys for r in records):raise ValueError('Snapshot keys changed')
    arrays={k:np.stack([r[k] for r in records]) for k in sorted(keys)}
    if any(not np.isfinite(a).all() for a in arrays.values()):raise ValueError('Nonfinite transition state')
    np.savez_compressed(out/'transition-states.npz',**arrays)
    atomic_json(out/'transition-states.json',{
        'schema_version':1,'count':len(records),'frame':'root/target environment_local; orientations and velocities world axes',
        'joint_names':list(env.robot.joint_names),'contact_body_names':list(env.contacts.body_names),
        'records':[{'array_row':j,'env_index':int(r['env_index']),
                    'scenario_id':scenario_ids[int(r['env_index'])],
                    'episode_step':int(r['episode_steps']),
                    'completed_hops':int(r['completed_hops'])} for j,r in enumerate(records)],
        'scope':'Successful landing boundary before next control action; physical state preserved, next goal/bookkeeping active. Not a complete simulator checkpoint; reset/replay equivalence unvalidated.'})
