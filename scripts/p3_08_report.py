"""Verify P3-08 evaluation comparability and summarize development results."""
import json
from pathlib import Path
from p3_08_evaluate import evaluation_plan
from p3_04_train import gate
from audit_chained_evaluation import check
from audit_artifacts import digest
ROOT=Path(__file__).resolve().parents[1]


def build_report():
    training=[gate(f'p3-08-{condition}-seed{seed}',1,800,1024)
              for condition in ('mapped','strict') for seed in (1,2)]
    references={};rows=[]
    for item in evaluation_plan():
        p=ROOT/item['out'];check(p)
        read=lambda name:json.loads((p/name).read_text())
        run,report,scenarios=read('run.json'),read('evaluation.json'),read('scenarios.json')
        assert Path(run['checkpoint']['path'])==(ROOT/item['source']/'checkpoint-000800.pt').resolve()
        assert run['checkpoint']['sha256']==digest(Path(run['checkpoint']['path']))
        contract={'episodes':scenarios['episodes'],'support':run['evaluation_support'],
                  'chain':run['chain_contract'],'action':run['action_evaluation']}
        key=item['suite']
        if key in references:assert contract==references[key],(key,item['condition'],item['seed'])
        else:references[key]=contract
        if key in ('mapped3','strict2'):
            plan=read('geometric-plan.json')
            assert plan['status']=='planned' and [c['forward_m'] for c in plan['contacts']]==([.15,.30,.45] if key=='mapped3' else [.15,.30])
            assert digest(p/'geometric-plan.json')==run['artifacts']['geometric-plan.json']
        manifest_paths=list((ROOT/'result').glob('*__'+p.name+'/manifest.json'));assert len(manifest_paths)==1
        mp=manifest_paths[0];m=json.loads(mp.read_text());assert digest(mp.parent/m['video'])==m['source_video_sha256']
        assert m['checkpoint']==run['checkpoint'] and 'phase:P3' in m['research_tags']
        replay=read('replay.json');assert len(replay['visible_env_ids'])==64 and replay['camera']['framing_side']==4
        by_goal={}
        for scenario,episode in zip(scenarios['episodes'],report['results']):
            assert scenario['id']==episode['scenario_id']
            goal=str(scenario['goal_forward_m']);v=by_goal.setdefault(goal,{'episodes':0,'successes':0})
            v['episodes']+=1;v['successes']+=int(episode['success'])
        row={k:item[k] for k in ('condition','seed','suite','out')}
        row.update({
            'episodes':report['episodes'],'successes':report['successes'],
            'completed_hops_histogram':report['completed_hops_histogram'],'by_goal':by_goal,
            'video_manifest':str(mp.relative_to(ROOT))})
        rows.append(row)
    return {'training':training,'new_training_steps':sum(r['new_steps'] for r in training),
            'comparability':'same scenarios, terrain, chain and action contracts within each suite; plan and video hashes verified',
            'scope':'two preselected development seeds, not final-test generalization','evaluations':rows}


if __name__=='__main__':
    r=build_report();(ROOT/'docs/p3-08-comparison.json').write_text(json.dumps(r,indent=2)+'\n')
    lines=['# P3-08 개발 평가 비교','','조건 | seed | mapped3 | strict2 | continuous','--- | --- | --- | --- | ---']
    for condition in ('parent','mapped','strict'):
        for seed in (1,2):
            scores=[next(e['successes'] for e in r['evaluations'] if e['condition']==condition and e['seed']==seed and e['suite']==suite) for suite in ('mapped3','strict2','continuous')]
            lines.append(f'{condition} | {seed} | '+' | '.join(f'{v}/64' for v in scores))
    lines+=['',r['scope'],'',f"새 학습 {r['new_training_steps']:,}step. smoke/profile 별도. 기하학적 계획 가능성과 실제 완주 성공은 구분한다."]
    (ROOT/'docs/p3-08-comparison.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
