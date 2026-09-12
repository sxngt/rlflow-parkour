"""Audit continuous shared-course records against physics-rate traces."""
import json,sys
from pathlib import Path
import numpy as np
from audit_artifacts import audit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from parkour.flight_trace import reconstruct_flights

def check(path):
    path=Path(path);audit(path)
    run=json.loads((path/'run.json').read_text());r=json.loads((path/'evaluation.json').read_text())
    assert run['config']['task']=='a1_continuous_tracker_v1'
    with np.load(path/'motion-trace.npz') as data:z={k:data[k] for k in data.files}
    assert np.allclose(np.diff(z['time']),.005,atol=1e-8)
    for i,row in enumerate(r['results']):
        valid=z['valid'][:,i];assert valid.sum()==row['length']*4
        indices=z['target_indices'][valid,i];accepted=z['accepted_indices'][valid,i]
        assert np.all(np.diff(indices,axis=0)>=0) and np.all(np.diff(accepted,axis=0)>=0)
        assert np.all(accepted<=indices)
        assert np.all(accepted[:,1]<=accepted[:,0])
        assert np.all(np.isfinite(z['root_pos'][valid,i]))
        if 'root_velocity_world' in z:
            events=reconstruct_flights(z['force'][valid,i],z['root_pos'][valid,i,2],
                z['root_velocity_world'][valid,i,2],z['nonfoot_force_max'][valid,i],.005)
            assert sum(e['counted_jump'] for e in events)==row['measured_jump_count']
            assert int(z['measured_jump_count'][valid,i][-1])==row['measured_jump_count']
            if 'clean_airborne_count' in row:
                assert sum(e['air_seconds']>=.02-1e-7 and not e['nonfoot_collision'] for e in events)==row['clean_airborne_count']
        if 'active_motion_seconds' in row:
            measured=float((np.linalg.norm(z['root_velocity'][valid,i],axis=-1)>.15).sum()*.005)
            assert abs(measured-row['active_motion_seconds'])<.011
        if 'travel_motion_seconds' in row:
            traveling=~(z['target_indices'][valid,i]==r['required_final_index']).all(axis=-1)
            measured=float(((np.linalg.norm(z['root_velocity'][valid,i],axis=-1)>.15)&traveling).sum()*.005)
            assert abs(measured-row['travel_motion_seconds'])<.011
        if row['success']:
            assert row['front_accepted_index']==row['rear_accepted_index']==r['required_final_index']
            assert row['final_hold_steps']>=10
    return {'run':str(path),'episodes':r['episodes'],'successes':r['successes'],'audit':'passed',
            'scope':'Artifact/first-episode trace/progress consistency; physical success gates remain separately instrumented'}
if __name__=='__main__':
    for p in sys.argv[1:]:print(json.dumps(check(p)))
