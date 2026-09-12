"""First-hop reward decomposition with terminal step included."""
import json
from pathlib import Path
import numpy as np
from p2_41_report import inspect,ROOT


def summarize(seed):
    inspect(seed)
    p=ROOT/f'artifacts/p2-41-reward-seed{seed}-retry1'
    load=lambda name:json.loads((p/name).read_text())
    events=load('chain-events.json')
    names=load('reward-components.json')['names']
    gamma=load('config.json')['runner']['algorithm']['gamma']
    hops=sorted((h for h in events['hops'] if h['segment']==0),key=lambda h:h['env_index'])
    assert len(hops)==64 and [h['env_index'] for h in hops]==list(range(64))
    rows=[]
    with np.load(p/'reward-components.npz') as data:
        for h in hops:
            i=h['env_index'];end=h['episode_step'];m=h['metrics']
            assert data['active'][:end,i].all()
            components=data['components'][:end,i].astype(np.float64)
            actual=data['reward'][:end,i].astype(np.float64)
            assert np.allclose(actual.sum(),m['return'],atol=2e-4,rtol=2e-6)
            rows.append(dict(env_index=i,success=m['success'],timeout=m['timeout'],steps=end,
                flight_forward_m=m['flight_forward_m'],components=dict(zip(names,components.sum(axis=0).tolist())),
                actual_return=float(actual.sum()),discounted_return=float((actual*gamma**np.arange(end)).sum())))
    return dict(seed=seed,gamma=gamma,episodes=rows,
        mean_components={k:float(np.mean([r['components'][k] for r in rows])) for k in names},
        mean_return=float(np.mean([r['actual_return'] for r in rows])),
        mean_discounted_return=float(np.mean([r['discounted_return'] for r in rows])),
        mean_steps=float(np.mean([r['steps'] for r in rows])))

if __name__=='__main__':
    rows=[summarize(s) for s in (1,3)]
    (ROOT/'docs/p2-41-first-hop.json').write_text(json.dumps(dict(
        scope='first maneuver only; same task but different fixed policies; discounted observed rewards exclude critic bootstrap',results=rows),indent=2)+'\n')
    for r in rows:print({k:v for k,v in r.items() if k!='episodes'})
