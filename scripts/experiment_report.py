"""Descriptive, first-episode research reports from an explicit run manifest."""
import argparse,json
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def summarize(entry):
 train=ROOT/'artifacts'/entry['run'];ev=train.with_name(train.name+'__final-evaluation')
 meta=json.loads((ev/'run.json').read_text());r=json.loads((ev/'evaluation.json').read_text())
 d=json.loads((ev/'diagnostics.json').read_text());sc=json.loads((ev/'scenarios.json').read_text())
 metrics=[json.loads(s) for s in (train/'metrics.jsonl').read_text().splitlines()]
 assert meta['status']=='SUCCEEDED' and json.loads((train/'run.json').read_text())['status']=='SUCCEEDED'
 assert metrics[-1]['iteration']==entry.get('updates',800)
 with np.load(ev/'motion-trace.npz') as trace:
  a={key:trace[key] for key in ('valid','stage','phase','foot_pos')}
 count=r['episodes'];last=[np.flatnonzero(a['valid'][:,i])[-1] for i in range(count)]
 terminal=Counter((int(a['stage'][t,i]),int(a['phase'][t,i])) for i,t in enumerate(last))
 row={**entry,'episodes':count,'successes':r['successes'],'mean_contacts':r['mean_completed_contacts'],
      'required_contacts':r['required_contacts'],'placed':sum(x['completed_contacts']==r['required_contacts'] for x in r['results']),
      'failures':sum(x['failure'] for x in r['results']),'timeouts':sum(x['timeout'] for x in r['results']),
      'flight_episodes':d['flight_episode_count'],'diagnostic_means':d['means'],
      'terminal_stage_phase':{f'{s}:{p}':n for (s,p),n in sorted(terminal.items())},
      'environment_steps':metrics[-1]['total_environment_steps'],
      'attempt_environment_steps':len(metrics)*meta['config']['runner']['num_steps_per_env']*json.loads((train/'run.json').read_text())['config']['num_envs'],
      'train_wall_seconds':json.loads(train.with_suffix('.supervisor.json').read_text())['wall_seconds']}
 if r['required_contacts']==1:
  names=['FL','FR','RL','RR']
  active=np.array([names.index(x['active_foot'].replace('_foot','')) for x in sc['episodes']]) if entry['foot']=='ALL' else np.full(count,names.index(entry['foot']))
  target=np.tile(np.array(meta['nominal_foot_xy_m']),(count,1,1))
  target[np.arange(count),active]+=np.array([x['foot_offsets_xy_m'][int(f)] for x,f in zip(sc['episodes'],active)])
  pos=np.array([a['foot_pos'][t,i,:,:2] for i,t in enumerate(last)])
  errors=np.linalg.norm(pos-target,axis=2)
  row['terminal_foot_error_mean_m']=dict(zip(['FL','FR','RL','RR'],errors.mean(axis=0).tolist()))
  row['terminal_all_feet_in_radius']=int((errors<=meta['config']['success_radius_m']).all(axis=1).sum())
 if 'by_foot' in r:
  row['by_foot']=r['by_foot']
  for foot,values in row['by_foot'].items():
   ids=[i for i,x in enumerate(r['results']) if x['active_foot']==foot]
   values['flight_episodes']=sum(d['results'][i]['has_flight_20ms'] for i in ids)
   states=Counter((int(a['stage'][last[i],i]),int(a['phase'][last[i],i])) for i in ids)
   values['terminal_stage_phase']={f'{stage}:{phase}':n for (stage,phase),n in sorted(states.items())}
   if r['required_contacts']==1:
    values['terminal_foot_error_mean_m']=dict(zip(['FL','FR','RL','RR'],errors[ids].mean(axis=0).tolist()))
    values['terminal_all_feet_in_radius']=int((errors[ids]<=meta['config']['success_radius_m']).all(axis=1).sum())
 return row,metrics,sc['episodes']

def main():
 p=argparse.ArgumentParser();p.add_argument('spec',type=Path);args=p.parse_args();spec=json.loads(args.spec.read_text())
 feet=list(dict.fromkeys(x['foot'] for x in spec['runs']));fig,axes=plt.subplots(len(feet),2,figsize=(12,4*len(feet)),squeeze=False)
 rows=[];scenarios={}
 for entry in spec['runs']:
  row,m,sc=summarize(entry);rows.append(row);foot=entry['foot']
  if foot in scenarios:assert scenarios[foot]==sc,'Evaluation targets differ within foot'
  else:scenarios[foot]=sc
  for j,key in enumerate(['mean_completed_contacts','success_rate']):
   vals=[x.get(key,np.nan) if j==0 else x['successes']/x['episodes'] if x['episodes'] else np.nan for x in m]
   axes[feet.index(foot),j].plot([x['iteration'] for x in m],vals,label=f"{entry['condition']} seed {entry['seed']}",linewidth=1,alpha=.75)
 for fi,foot in enumerate(feet):
  for j,title in enumerate(['completed contacts','training episode success']):
   ax=axes[fi,j];ax.set_title(f'{foot}: {title}');ax.set_xlabel('PPO update');ax.grid(alpha=.2);ax.legend(fontsize=8)
 stem=spec['report'];fig.tight_layout();fig.savefig(ROOT/f'docs/figures/{stem}-learning.png',dpi=160);plt.close(fig)
 total=sum(x['attempt_environment_steps'] for x in rows);new=sum(x['attempt_environment_steps'] for x in rows if not x.get('reused'))
 lines=[f"# {spec['title']}",'',spec['description'],'',f"비교 전체 {total:,} 환경 step, 신규 {new:,}step. [사전 프로토콜]({spec['protocol']}).",'',
 '| 발 | 조건 | seed | 안정화 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |','|---|---|---:|---:|---:|---:|---:|---:|']
 for x in rows:lines.append(f"| {x['foot']} | {x['condition']} | {x['seed']} | {x['successes']}/{x['episodes']} | {x['placed']}/{x['episodes']} | {x['failures']}/{x['episodes']} | {x['timeouts']}/{x['episodes']} | {x['flight_episodes']}/{x['episodes']} |")
 if any('by_foot' in x for x in rows):
  lines+=['','## 공유 정책의 발별 평가','','| 조건 | seed | 이동 발 | 안정화 | 착지 | ≥20ms 전 발 무접촉 |','|---|---:|---|---:|---:|---:|']
  for x in rows:
   for foot,v in x.get('by_foot',{}).items():lines.append(f"| {x['condition']} | {x['seed']} | {foot} | {v['successes']}/{v['episodes']} | {v['placed']}/{v['episodes']} | {v['flight_episodes']}/{v['episodes']} |")
 lines+=['',f'![학습 곡선](figures/{stem}-learning.png)','',
 '학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.','', '## 종료 단계','']
 for x in rows:
  lines.append(f"- {x['foot']} {x['condition']} seed {x['seed']}: `{x['terminal_stage_phase']}`")
  for foot,v in x.get('by_foot',{}).items():lines.append(f"  - {foot}: `{v['terminal_stage_phase']}`")
 lines+=['','## 해석 및 다음 판단','']+spec.get('findings',['분석 중. 표만으로 모델 승격을 결정하지 않는다.'])
 lines+=['','## 범위·재현','',
 '개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종16대병렬영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.','',
 f"실행 목록 및 보고서 명세: `{args.spec}`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다."]
 (ROOT/f'docs/{stem}-results.md').write_text('\n'.join(lines)+'\n');(ROOT/f'docs/{stem}-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps([{k:x[k] for k in ['foot','condition','seed','successes','placed','flight_episodes']} for x in rows],indent=2))
if __name__=='__main__':main()
