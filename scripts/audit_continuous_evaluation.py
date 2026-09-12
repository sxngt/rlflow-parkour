"""Audit continuous shared-course records against physics-rate traces."""
import json,sys
from pathlib import Path
import numpy as np
from audit_artifacts import audit

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
        if row['success']:
            assert row['front_accepted_index']==row['rear_accepted_index']==r['required_final_index']
            assert row['final_hold_steps']>=10
    return {'run':str(path),'episodes':r['episodes'],'successes':r['successes'],'audit':'passed',
            'scope':'Artifact/first-episode trace/progress consistency; physical success gates remain separately instrumented'}
if __name__=='__main__':
    for p in sys.argv[1:]:print(json.dumps(check(p)))
