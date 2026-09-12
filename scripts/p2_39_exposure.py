"""Compare observed target exposure; reset probabilities are not step fractions."""
import json
from pathlib import Path
from audit_retention_training import check

ROOT = Path(__file__).resolve().parents[1]

def summarize(path):
    accounting = check(path)
    assert accounting['updates'] == 800
    run = json.loads((path / 'run.json').read_text())
    goals = run['config']['retention_training']['single_goal_choices_m']
    rows = [json.loads(x) for x in (path / 'metrics.jsonl').read_text().splitlines()]
    distances = []
    for i, goal in enumerate(goals):
        distances.append(dict(goal_m=goal,
            single_steps=sum(r['single_goal_environment_steps'][i] for r in rows),
            reset_draws_including_initial=run['single_goal_initial_draws'][i] + sum(r['single_goal_reset_draws'][i] for r in rows)))
    assert sum(r['single_steps'] for r in distances) == 9830400
    native = json.loads((path.with_name(path.name + '__final-evaluation') / 'chain-events.json').read_text())
    first = [h['metrics'] for h in native['hops'] if h['segment'] == 0]
    flights = [r['flight_forward_m'] for r in first if r['flight_touch_recorded']]
    return dict(run=str(path.relative_to(ROOT)), distances=distances,
        chain_first_steps=accounting['task_hop_environment_steps'][0][0],
        chain_second_steps=accounting['task_hop_environment_steps'][0][1],
        first_hop_recorded_flights=len(flights),
        first_hop_flight_min_m=min(flights) if flights else None,
        first_hop_flight_max_m=max(flights) if flights else None)

if __name__ == '__main__':
    result=[]
    for seed in range(4):
        a=summarize(ROOT/f'artifacts/p2-38-continuous-seed{seed}')
        b=summarize(ROOT/f'artifacts/p2-39-coverage-seed{seed}')
        at=next(x['single_steps'] for x in a['distances'] if x['goal_m']==.15)
        bt=next(x['single_steps'] for x in b['distances'] if x['goal_m']==.15)
        result.append(dict(seed=seed, endpoint=a, coverage=b, single_15cm_step_ratio=bt/at))
    output=dict(scope='Observed on-policy exposure and final mean-policy development diagnostics; not causal identification or reward-component attribution', pairs=result)
    (ROOT/'docs/p2-39-exposure.json').write_text(json.dumps(output,indent=2)+'\n')
    for r in result:print(r['seed'],r['single_15cm_step_ratio'],r['endpoint']['chain_second_steps'],r['coverage']['chain_second_steps'])
