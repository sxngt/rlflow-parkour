"""Snapshot complete curriculum blocks only; keep pending seeds explicit."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[]
keys=('episodes','successes','failures','valid_flights','landed_episodes')
for source in ('p2-24-deck','p2-27-continuous'):
 for seed in range(4):
  p=ROOT/'artifacts'/f'{source}-seed{seed}'
  meta=json.loads((p/'run.json').read_text());f=p/'metrics.jsonl'
  metrics=[json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []
  block=[m for m in metrics if 1<=m['iteration']<=400]
  if len(block)!=400:
   rows.append({'run':p.name,'seed':seed,'complete':False,'observed_updates':len(block),'totals':None});continue
  assert [m['iteration'] for m in block]==list(range(1,401))
  assert all(m['train_forward_range_m']==[0.,.05] and m['launch_radius_m']==.06 and m['exploration_std_cap']==.35 for m in block)
  rows.append({'run':p.name,'seed':seed,'complete':True,'observed_updates':400,'totals':{k:sum(m[k] for m in block) for k in keys}})
payload={'scope':'First 400 updates, sampled training-policy terminated episodes. Not fixed-policy evaluation; different policies produce different episode counts. Pending rows excluded from totals and never treated as zero performance. No seed-pooled improvement claim.', 'rows':rows}
(ROOT/'docs/p2-27-first-stage.json').write_text(json.dumps(payload,indent=2)+'\n')
lines=['# P2-27 첫 학습 구간 관측','', '업데이트1–400만 비교한다. 각 구간9,830,400 환경step이며 episode 수는 정책에 따라 다르다. 학습 중 sampled 행동의 종료 episode 통계이며 고정 평가 성공률이 아니다. 미완료 seed를 성공0으로 취급하지 않는다.','', '| run | 완료 | episode | 성공 | 실패 | 유효비행 | 재접촉 |','|---|---|---:|---:|---:|---:|---:|']
for r in rows:
 t=r['totals'];lines.append('| '+r['run']+' | '+('완료 | '+' | '.join(str(t[k]) for k in keys) if t else '미완료 | — | — | — | — | —')+' |')
(ROOT/'docs/p2-27-first-stage.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
