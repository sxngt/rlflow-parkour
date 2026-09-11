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
 train=ROOT/'artifacts'/entry['run'];ev=ROOT/'artifacts'/entry.get('evaluation_run',train.name+'__final-evaluation')
 meta=json.loads((ev/'run.json').read_text());r=json.loads((ev/'evaluation.json').read_text())
 d=json.loads((ev/'diagnostics.json').read_text());sc=json.loads((ev/'scenarios.json').read_text())
 metrics=[json.loads(s) for s in (train/'metrics.jsonl').read_text().splitlines()]
 assert meta['status']=='SUCCEEDED' and json.loads((train/'run.json').read_text())['status']=='SUCCEEDED'
 assert metrics[-1]['iteration']==entry.get('updates',800)
 with np.load(ev/'motion-trace.npz') as trace:
  keys=['valid','stage','phase','foot_pos']
  if meta['config'].get('jump'):keys+=['force','time','root_z','root_vz']
  if meta['config'].get('jump',{}).get('evaluation_forward_m') is not None:keys+=['root_xy']
  a={key:trace[key] for key in keys}
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
 if meta['config'].get('jump'):
  import sys
  sys.path.insert(0,str(ROOT/'src'))
  from parkour.diagnostics import jump_first_touches
  first=jump_first_touches(a,meta['nominal_foot_xy_m'],sc['episodes'],meta['config']['jump']['landing_radius_m'])
  row['first_touch_all_within']=sum(x['all_within'] for x in first)
  post=a['valid']&(a['stage']==2)
  if post.any():
   forces=np.linalg.norm(a['force'][post],axis=-1)
   row['post_touch_physics']={'vertical_velocity_rms_m_s':float(np.sqrt(np.mean(a['root_vz'][post]**2))),
    'all_feet_below_2N_fraction':float((forces<2).all(axis=1).mean()),
    'all_feet_above_5N_fraction':float((forces>5).all(axis=1).mean())}

  row['first_touch_samples']=first
  fixed_vz=[];fixed_force=[];window_samples=int(round(.2*d['physics_hz']))
  for i,sample in enumerate(first):
   times=[t for t in sample['times_s'] if t is not None]
   if not times:continue
   start=int(np.searchsorted(a['time'],min(times)));stop=start+window_samples
   if stop<=len(a['time']) and a['valid'][start:stop,i].all():
    fixed_vz.append(a['root_vz'][start:stop,i]);fixed_force.append(np.linalg.norm(a['force'][start:stop,i],axis=-1))
  row['first_touch_200ms']={'complete_episodes':len(fixed_vz),'definition':f'{window_samples} physics samples from first post-flight foot contact; incomplete windows excluded and counted.'}
  if fixed_vz:
   v=np.stack(fixed_vz);f=np.stack(fixed_force)
   row['first_touch_200ms'].update(vertical_velocity_rms_m_s=float(np.sqrt(np.mean(v**2))),
    all_feet_below_2N_fraction=float((f<2).all(axis=2).mean()),all_feet_above_5N_fraction=float((f>5).all(axis=2).mean()))

  if 'by_distance' in r:
   row['by_distance']=r['by_distance']
   row['launch_radius_m']=meta['config']['jump']['launch_radius_m']
   origin=np.asarray(meta['stance_calibration']['root_state'][:2])
   distances=[float(np.linalg.norm(np.asarray([record['launch_root_x_m'],record['launch_root_y_m']])-origin)) if record['launch_recorded'] else None for record in r['results']]
   row['launch_displacement_m']=distances
   row['recorded_launches_within_3cm']=sum(d is not None and d<=.03 for d in distances)
   row['successful_trajectories_within_3cm']=sum(record['success'] and d is not None and d<=.03 for record,d in zip(r['results'],distances))
   for i,(sample,record) in enumerate(zip(first,r['results'])):
    if record['launch_recorded']:
     stages=np.flatnonzero(a['valid'][:,i]&(a['stage'][:,i]>=1))
     launch_index=int(stages[0]-1) if len(stages) else last[i]
     assert launch_index>=0
     assert np.allclose(a['root_xy'][launch_index,i],[record['launch_root_x_m'],record['launch_root_y_m']],atol=1e-5,rtol=0),'Launch root differs from trace'
    if record['flight_touch_recorded']:
     touch_index=int(np.searchsorted(a['time'],min(t for t in sample['times_s'] if t is not None)))
     assert np.allclose(a['root_xy'][touch_index,i],[record['first_touch_root_x_m'],record['first_touch_root_y_m']],atol=1e-5,rtol=0),'First-touch root differs from trace'
  row['first_touch_by_foot']={}
  for i,name in enumerate(['FL','FR','RL','RR']):
   errors=[sample['errors_m'][i] for sample in first if sample['errors_m'][i] is not None]
   row['first_touch_by_foot'][name]={'observed':len(errors),'mean_error_m':float(np.mean(errors)) if errors else None,
    'within_radius':sum(e<=meta['config']['jump']['landing_radius_m'] for e in errors)}
  if 'first_touch_count' in r['results'][0]:
   row['stabilized_once']=sum(x['stabilized_once'] for x in r['results'])
   row['online_first_touch_all_within']=sum(x['first_touch_all_within'] for x in r['results'])
   for sample,record in zip(first,r['results']):
    for foot,error in zip(['fl','fr','rl','rr'],sample['errors_m']):
     actual=record[f'first_touch_error_{foot}_m']
     assert (actual==-1 if error is None else abs(actual-error)<1e-5),'Online first touch differs from raw physics trace'
  terminal_rise=np.array([a['root_z'][t,i] for i,t in enumerate(last)])-meta['stance_calibration']['root_state'][2]
  row['mean_terminal_base_rise_m']=float(terminal_rise.mean())
  row['terminal_height_outside_tolerance']=int((np.abs(terminal_rise)>meta['config']['jump']['final_height_error_max_m']).sum())
  row['apex_command_met']=sum(x['valid_flight'] and x['flight_apex_rise_m']>=x['required_apex_m'] for x in r['results'])
  row['terminal_stable_steps_histogram']=dict(sorted(Counter(str(x['final_stable_steps']) for x in r['results']).items()))
  if 'final_supported' in r['results'][0]:
   spec=meta['config']['jump']
   row['terminal_gate_violations']={
    'height':sum(abs(x['final_height_error_m'])>spec['final_height_error_max_m'] for x in r['results']),
    'vertical_speed':sum(abs(x['final_vz_m_s'])>spec['final_vz_max_m_s'] for x in r['results']),
    'angular_speed':sum(x['final_angular_speed_rad_s']>spec['final_angular_speed_max_rad_s'] for x in r['results']),
    'foot_target':sum(not x['final_all_feet_in_radius'] for x in r['results']),
    'contact_state':sum(not x['final_contact_all'] for x in r['results']),
    'support_history':sum(not x['final_supported'] for x in r['results'])}

  row['first_touch_definition']='First >5N foot force at 200Hz after valid-flight stage, foot body-center XY; supplemental metric, not the original success gate.'
 for key in ['valid_flights','landed_episodes','mean_flight_apex_rise_m','nonfoot_collisions']:
  if key in r:row[key]=r[key]
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
 total=sum({x['run']:x['attempt_environment_steps'] for x in rows}.values());new=sum({x['run']:x['attempt_environment_steps'] for x in rows if not x.get('reused')}.values())
 lines=[f"# {spec['title']}",'',spec['description'],'',f"고유 학습 run 기준 {total:,} 환경 step, 신규 {new:,}step. [사전 프로토콜]({spec['protocol']}).",'',
 '| 발 | 조건 | seed | 안정화 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for x in rows:lines.append(f"| {x['foot']} | {x['condition']} | {x['seed']} | {x['successes']}/{x['episodes']} | {x['placed']}/{x['episodes']} | {x['failures']}/{x['episodes']} | {x['timeouts']}/{x['episodes']} | {x['flight_episodes']}/{x['episodes']} |")
 if any('valid_flights' in x for x in rows):
  lines+=['','## 도약 계약 지표','','| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 최종 안정화 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
  for x in rows:
   if 'valid_flights' in x:lines.append(f"| {x['condition']} | {x['seed']} | {x['valid_flights']}/{x['episodes']} | {x['landed_episodes']}/{x['episodes']} | {x['successes']}/{x['episodes']} | {x['nonfoot_collisions']} | {100*x['mean_flight_apex_rise_m']:.2f} cm | {x['apex_command_met']}/{x['episodes']} | {x['first_touch_all_within']}/{x['episodes']} | {x['terminal_height_outside_tolerance']}/{x['episodes']} |")
 if any('first_touch_by_foot' in x for x in rows):
  lines+=['','## 발별 첫 접촉','','오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.','', '| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |','|---|---:|---|---:|---:|---:|']
  for x in rows:
   for foot,v in x.get('first_touch_by_foot',{}).items():
    error='N/A' if v['mean_error_m'] is None else f"{100*v['mean_error_m']:.2f} cm"
    lines.append(f"| {x['condition']} | {x['seed']} | {foot} | {v['observed']}/{x['episodes']} | {error} | {v['within_radius']}/{x['episodes']} |")
 if any('stabilized_once' in x for x in rows):
  lines+=['','## 공통 지표 분리','','| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |','|---|---:|---:|---:|']
  for x in rows:lines.append(f"| {x['condition']} | {x['seed']} | {x.get('stabilized_once',x['successes'])}/{x['episodes']} | {x['first_touch_all_within']}/{x['episodes']} |")
 if any('by_distance' in x for x in rows):
  lines+=['','## 출발 계약과 궤적 부분집합','','3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.','','| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |','|---|---:|---:|---:|---:|']
  for x in rows:
   if 'launch_radius_m' in x:lines.append(f"| {x['condition']} | {x['seed']} | {100*x['launch_radius_m']:g} cm | {x['recorded_launches_within_3cm']}/{x['episodes']} | {x['successful_trajectories_within_3cm']}/{x['episodes']} |")
  lines+=['','## 거리별 평가','','| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |','|---|---:|---:|---:|---:|---:|---:|---:|']
  for x in rows:
   for distance,v in x.get('by_distance',{}).items():lines.append(f"| {x['condition']} | {x['seed']} | {100*float(distance):g} cm | {v['successes']}/{v['episodes']} | {v['launches_in_region']}/{v['episodes']} | {v['travel_met']}/{v['episodes']} | {v['first_touch_precise']}/{v['episodes']} | {v['stabilized']}/{v['episodes']} |")
 if any('by_foot' in x for x in rows):
  lines+=['','## 공유 정책의 발별 평가','','| 조건 | seed | 이동 발 | 안정화 | 착지 | ≥20ms 전 발 무접촉 |','|---|---:|---|---:|---:|---:|']
  for x in rows:
   for foot,v in x.get('by_foot',{}).items():lines.append(f"| {x['condition']} | {x['seed']} | {foot} | {v['successes']}/{v['episodes']} | {v['placed']}/{v['episodes']} | {v['flight_episodes']}/{v['episodes']} |")
 lines+=['',f'![학습 곡선](figures/{stem}-learning.png)','',
 '학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.','', '## 종료 단계','']
 for x in rows:
  lines.append(f"- {x['foot']} {x['condition']} seed {x['seed']}: `{x['terminal_stage_phase']}`")
  for foot,v in x.get('by_foot',{}).items():lines.append(f"  - {foot}: `{v['terminal_stage_phase']}`")
 if any('terminal_gate_violations' in x for x in rows):
  lines+=['','## 마지막 제어 표본의 안정화 조건 위반','','복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.','']
  for x in rows:
   if 'terminal_gate_violations' in x:lines.append(f"- {x['condition']} seed {x['seed']}: `{x['terminal_gate_violations']}`")
 lines+=['','## 해석 및 다음 판단','']+spec.get('findings',['분석 중. 표만으로 모델 승격을 결정하지 않는다.'])
 lines+=['','## 범위·재현','',
 '개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종 병렬 평가 영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.','',
 f"실행 목록 및 보고서 명세: `{args.spec}`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다."]
 if spec.get('success_label'):
  lines=[line.replace('안정화 성공',spec['success_label']).replace('최종 안정화 |',spec['success_label']+' |') for line in lines]
 (ROOT/f'docs/{stem}-results.md').write_text('\n'.join(lines)+'\n');(ROOT/f'docs/{stem}-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps([{k:x[k] for k in ['foot','condition','seed','successes','placed','flight_episodes']} for x in rows],indent=2))
if __name__=='__main__':main()
