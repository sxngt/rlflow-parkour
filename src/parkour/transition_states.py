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


def restore_transition_states(env, source, checkpoint, support):
    """Restore measured articulation and explicit controller state for a probe.

No solver-state equivalence is asserted. Only matching, complete first landing
sets can be used by this initial implementation.
"""
    import json
    import torch
    from parkour.runtime import sha256
    source = source.resolve()
    run = json.loads((source/'run.json').read_text())
    meta = json.loads((source/'transition-states.json').read_text())
    if run['status'] != 'SUCCEEDED' or run['checkpoint']['sha256'] != sha256(checkpoint):
        raise ValueError('Restore requires the same verified policy checkpoint')
    if run['evaluation_support'] != support or run['chain_contract']['settle_command'] != env.chain_settle_mode:
        raise ValueError('Restore terrain or preparation contract changed')
    for name in ('transition-states.json','transition-states.npz'):
        if sha256(source/name) != run['artifacts'][name]:raise ValueError('Snapshot hash mismatch')
    if meta['count'] != env.num_envs or meta['joint_names'] != list(env.robot.joint_names) or meta['contact_body_names'] != list(env.contacts.body_names):
        raise ValueError('Snapshot population or articulation names differ')
    with np.load(source/'transition-states.npz',allow_pickle=False) as file:
        order=np.argsort(file['env_index'])
        if not np.array_equal(file['env_index'][order],np.arange(env.num_envs)):
            raise ValueError('Exactly one snapshot per environment required')
        data={k:torch.as_tensor(file[k][order].copy(),device=env.device) for k in file.files}
    if not bool((data['completed_hops']==1).all()):raise ValueError('Only first landing supported')
    root=data['root'].clone();root[:,:3]+=env.scene.env_origins
    env.robot.write_root_pose_to_sim(root[:,:7])
    env.robot.write_root_velocity_to_sim(root[:,7:])
    env.robot.write_joint_state_to_sim(data['joint_pos'],data['joint_vel'])
    env.actions.copy_(data['actions']);env.previous_actions.copy_(data['previous_actions'])
    env.settle_action.copy_(data['actions']);env.contact_on.copy_(data['contact_on'])
    env.contacts.data.net_forces_w_history.copy_(data['contact_history'])
    env.episode_length_buf.copy_(data['episode_steps'])
    env.chain.completed.copy_(data['completed_hops'])
    env.chain.start_step.copy_(data['episode_steps'])
    env.chain.launch_origin.copy_(data['launch_origin_xy'])
    env.required_apex.copy_(data['required_apex'])
    offsets=torch.zeros(env.num_envs,4,2,device=env.device);offsets[:,:,0]=.30
    env.set_sequence_offsets(offsets);env.goal_distance.fill_(.15)
    observed=env._get_observations()['policy']
    error=(observed-data['post_transition_observation']).abs()
    return {'source':str(source),'snapshot_sha256':sha256(source/'transition-states.npz'),
            'initial_observation_max_abs_error':float(error.max()),
            'initial_observation_error_per_env':error.max(dim=1).values.tolist(),
            'source_episode_steps':data['episode_steps'].tolist(),
            'restored_prior_hops':1,
            'scope':'Restored final hop only; not an end-to-end course evaluation. Solver warm-start not restored.'}
