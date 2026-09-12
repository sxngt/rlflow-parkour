"""Account for discrete goal draws and actual PPO environment transitions."""
import argparse
import json
from pathlib import Path
from audit_artifacts import audit

ROOT=Path(__file__).resolve().parents[1]


def summarize(path):
    audit(path)
    meta=json.loads((path/'run.json').read_text());config=meta['config'];jump=config['jump']
    if jump.get('distance_curriculum') or jump.get('launch_curriculum'):
        raise ValueError('Exposure audit currently requires fixed curricula')
    values=jump.get('train_forward_choices_m')
    if values is None:
        low,high=jump['train_forward_range_m']
        if low!=high:raise ValueError('Only finite discrete goals are counted')
        values=[low]
    keys=list(map(str,values));initial=meta['goal_accounting_initial_draws']
    assert set(initial)==set(keys)
    metrics=[json.loads(line) for line in (path/'metrics.jsonl').read_text().splitlines()]
    steps={k:0 for k in keys};draws={k:0 for k in keys}
    for row in metrics:
        assert set(row['goal_environment_steps'])==set(row['goal_reset_draws'])==set(keys)
        assert sum(row['goal_environment_steps'].values())==config['num_envs']*config['runner']['num_steps_per_env']
        assert sum(row['goal_reset_draws'].values())==row['episodes']
        for key in keys:
            for field in ('goal_environment_steps','goal_reset_draws'):
                assert type(row[field][key]) is int and row[field][key]>=0
            steps[key]+=row['goal_environment_steps'][key];draws[key]+=row['goal_reset_draws'][key]
    total=sum(steps.values());new=config['num_envs']*config['runner']['num_steps_per_env']*len(metrics)
    assert total==new
    return {'run':path.name,'updates_in_attempt':len(metrics),'new_environment_steps':new,
        'initial_reset_draws':initial,'rollout_reset_draws':draws,'environment_steps_by_goal':steps,
        'step_fraction_by_goal':{k:v/total for k,v in steps.items()},
        'reset_draw_fraction_by_goal':{k:(v+initial[k])/(sum(draws.values())+sum(initial.values())) for k,v in draws.items()},
        'contract':meta['goal_accounting_contract']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('spec',type=Path);args=parser.parse_args()
    spec=json.loads(args.spec.read_text());prefix=spec['report']
    if Path(prefix).name!=prefix:raise ValueError('Invalid report filename')
    names=sorted({r['run'] for r in spec['runs'] if not r.get('reused',False)})
    rows=[summarize(ROOT/'artifacts'/name) for name in names]
    output={'rows':rows,'new_environment_steps':sum(r['new_environment_steps'] for r in rows),
        'scope':'Only new runs selected by the manifest. Reset sampling probability is not a promise of equal transition counts; initial discarded resets are shown separately.'}
    (ROOT/f'docs/{prefix}-goal-exposure.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'runs':len(rows),'new_environment_steps':output['new_environment_steps']}))
