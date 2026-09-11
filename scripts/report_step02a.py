"""Single-foot screening; one training seed per foot, descriptive results only."""
import json
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]

def main():
 rows=[];fig,axes=plt.subplots(1,2,figsize=(12,4))
 for foot in ['fl','fr','rl','rr']:
  train=ROOT/f'artifacts/p1-step02a-single-{foot}-seed0';ev=train.with_name(train.name+'__final-evaluation')
  meta=json.loads((train/'run.json').read_text());r=json.loads((ev/'evaluation.json').read_text());d=json.loads((ev/'diagnostics.json').read_text())
  m=[json.loads(s) for s in (train/'metrics.jsonl').read_text().splitlines()]
  assert meta['status']=='SUCCEEDED' and m[-1]['iteration']==800 and m[-1]['total_environment_steps']==19660800
  assert r['required_contacts']==1 and all(x['completed_contacts'] in [0,1] for x in r['results'])
  trace=np.load(ev/'motion-trace.npz');last=[np.flatnonzero(trace['valid'][:,i])[-1] for i in range(r['episodes'])]
  evmeta=json.loads((ev/'run.json').read_text());sc=json.loads((ev/'scenarios.json').read_text())
  active=['FL','FR','RL','RR'].index(foot.upper());target=np.tile(np.array(evmeta['nominal_foot_xy_m']),(r['episodes'],1,1))
  target[:,active]+=np.array([s['foot_offsets_xy_m'][active] for s in sc['episodes']])
  finalpos=np.array([trace['foot_pos'][t,i,:,:2] for i,t in enumerate(last)])
  finalerrors=np.linalg.norm(finalpos-target,axis=2)
  terminal=Counter((int(trace['stage'][t,i]),int(trace['phase'][t,i])) for i,t in enumerate(last))
  row={'foot':foot.upper(),'seed':0,'episodes':r['episodes'],'successes':r['successes'],'placed':sum(x['completed_contacts']==1 for x in r['results']),
   'failures':sum(x['failure'] for x in r['results']),'timeouts':sum(x['timeout'] for x in r['results']),
   'terminal_foot_error_mean_m':dict(zip(['FL','FR','RL','RR'],finalerrors.mean(axis=0).tolist())),
   'terminal_all_feet_in_radius':int((finalerrors<=.025).all(axis=1).sum()),
   'mean_contacts':r['mean_completed_contacts'],'flight_episodes':d['flight_episode_count'],
   'root_vz_rms':float(np.sqrt(np.mean([x['mean_squared_vertical_speed'] for x in r['results']]))),
   'terminal_stage_phase':{f'{s}:{p}':n for (s,p),n in sorted(terminal.items())},'diagnostic_means':d['means']}
  rows.append(row)
  for ax,key in zip(axes,['mean_completed_contacts','success_rate']):
   values=[x.get(key,np.nan) if key!='success_rate' else x['successes']/x['episodes'] if x['episodes'] else np.nan for x in m]
   ax.plot([x['iteration'] for x in m],values,label=foot.upper(),linewidth=1,alpha=.8)
 for ax,title in zip(axes,['Training completed contacts (max 1)','Training terminated-episode success fraction']):
  ax.set_title(title);ax.set_xlabel('PPO update');ax.grid(alpha=.2);ax.legend()
 fig.tight_layout();fig.savefig(ROOT/'docs/figures/step02a-learning.png',dpi=160);plt.close(fig)
 lines=['# P1 · Step 02a — 발별 단독 이동 결과','',
  '[사전 프로토콜](step02a-protocol.md)에 따라 FL/FR/RL/RR를 각 seed 0, 1024환경, 800updates로 처음부터 학습했다. 총 78,643,200 환경 step. 별도 64개 개발 episode의 첫 종료만 평가했다.','',
  '| 이동 발 | 착지 후 안정화 성공 | 1회 착지 완료 | 낙상 | 시간초과 | 네 발 무접촉 ≥20ms | 수직 속도 RMS |','|---|---:|---:|---:|---:|---:|---:|']
 for r in rows:lines.append(f"| {r['foot']} | {r['successes']}/64 | {r['placed']}/64 | {r['failures']}/64 | {r['timeouts']}/64 | {r['flight_episodes']}/64 | {r['root_vz_rms']:.4f} m/s |")
 lines+=['','![학습 곡선](figures/step02a-learning.png)','',
  '학습 곡선은 해당 update에서 종료된 episode의 통계다. 고정 개발군 성공률과 구분한다. RMS는 episode별 평균 제곱 수직 속도의 평균에 제곱근을 취했다.','',
  '## 종료 직전 단계','', '200Hz 기록에서 각 환경의 마지막 유효 표본을 사용한다. `0:0`은 들기, `0:1`은 착지, `4:1`은 최종 안정화다. 최종 제어 이벤트 직전 표본일 수 있으므로 착지 완료 여부는 별도 terminal metrics를 우선한다.','']
 for r in rows:lines.append(f"- {r['foot']}: `{r['terminal_stage_phase']}`")
 lines+=['','## 해석 범위','',
  '발별 독립 학습 seed는 하나다. 발 간 결과 차이를 구조적 실행 가능성이나 통계적 우열로 단정하지 않는다. 단독 이동 성공은 4발 순차 이동이나 파쿠르 성공을 의미하지 않는다. 지지 조건은 lift/place 이벤트와 최종 안정화에 적용하며 모든 중간 시각의 3발 지지를 보장하는 제약은 아니다.',
  '', '최종 checkpoint를 사전 정의대로 평가했다. 실패와 영상도 보존하며 champion으로 자동 승격하지 않는다. 각 run의 정책·설정·계보·평가·200Hz NPZ는 `artifacts/p1-step02a-single-{fl,fr,rl,rr}-seed0` 및 `__final-evaluation`에 있다. 상세 제목의 최종 영상은 `result/`에 정리했다. 모니터링에서 `P1 / 02a·발별 단독 이동`과 발 조건 태그로 조회한다.']
 lines+=['','## 이번 결과의 판단','',
  '모든 조건에서 지정 발의 들기→착지는 64/64 완료했다. 안정화까지 성공한 횟수는 FL 0, FR 64, RL 0, RR 4였다. 순차 과제의 후반 단계 실패를 해당 발의 단독 이동 불능만으로 설명할 수 없다. 단독 정책과 순차 정책은 다르므로 순차 실행 가능성을 입증한 것은 아니다.',
  '', '마지막 유효 표본의 발별 수평 오차 평균은 다음과 같다. 판정 반경은 각 발 2.5cm이며 평균값만으로 개별 episode 성공을 판정하지 않는다.','',
  '| 이동 조건 | FL 오차 cm | FR 오차 cm | RL 오차 cm | RR 오차 cm | 네 발 모두 반경 내 |','|---|---:|---:|---:|---:|---:|']
 for r in rows:
  values=' | '.join(f'{v*100:.2f}' for v in r['terminal_foot_error_mean_m'].values())
  lines.append(f"| {r['foot']} | {values} | {r['terminal_all_feet_in_radius']}/64 |")
 lines+=['','FL 조건의 FR/RR 지지 발, RL 조건의 FL/RR 지지 발은 평균적으로 목표 반경을 벗어났다. RR 조건도 마지막 표본에서 네 발이 반경 내인 경우는 4/64였다. 이는 최종 발 위치 유지가 충족되지 않은 직접 관측이며 미끄러짐이라는 물리 원인을 확정하지 않는다.',
  '', 'RL 조건에서는 2/64 episode에 20ms 이상 네 발 무접촉이 있었다. 이벤트 순간 3발 지지 조건만으로 전체 궤적의 hopping을 제거하지 못한다.',
  '', '다음 비교 후보는 기존 보상을 대조군으로 두고 지지 발별 오차 및 최종 단계의 네 발 정렬 학습 신호를 명시한 보상이다. 현재의 지지 오차 평균은 개별 발 오차를 가릴 수 있지만, 보상 변경의 효과는 아직 검증하지 않았다. 추가 seed와 동일 예산 비교 후에 순차 연결을 시도한다.',
  '', '학습 4건과 자동 평가 4건의 checkpoint·artifact hash, GPU UUID 격리·자원 회수 감사를 통과했다. 합성 상태 검사, 단위 검사 15개, 모니터링 검사 6개, 프론트 빌드도 통과했다. 최종 영상 4개는 result와 웹에 등록했다.']
 (ROOT/'docs/step02a-results.md').write_text('\n'.join(lines)+'\n');(ROOT/'docs/step02a-summary.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
