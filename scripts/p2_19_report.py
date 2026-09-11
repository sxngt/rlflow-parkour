"""Paired frozen-policy action-sampling diagnostic report."""
import json
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1]

def main():
    rows=[];stds=[];paired=None
    for seed in range(4):
        source=ROOT/'artifacts'/f'p2-18-deck-seed{seed}'
        cp=torch.load(source/'checkpoint-001600.pt',map_location='cpu',weights_only=False)
        std=cp['model']['std'].tolist();stds.append({'seed':seed,'std_per_joint':std,'mean_std':sum(std)/len(std)})
        old=json.loads((source.with_name(source.name+'__final-evaluation')/'evaluation.json').read_text())
        old_scenarios=json.loads((source.with_name(source.name+'__final-evaluation')/'scenarios.json').read_text())
        for mode,rng in [('mean',20000),('sampled',20000),('sampled',20001)]:
            p=ROOT/'artifacts'/f'p2-19-seed{seed}-{mode}-rng{rng}'
            meta=json.loads((p/'run.json').read_text());report=json.loads((p/'evaluation.json').read_text())
            scenarios=json.loads((p/'scenarios.json').read_text());assert scenarios==old_scenarios
            assert meta['status']=='SUCCEEDED' and report['episodes']==64
            assert meta['action_evaluation']['mode']==mode
            assert meta['checkpoint']['sha256']==json.loads((source/'checkpoint-001600.json').read_text())['sha256']
            if mode=='mean':assert report['results']==old['results']
            else:assert meta['action_evaluation']['seed']==rng
            rows.append({'seed':seed,'mode':mode,'rng':rng if mode=='sampled' else None,'run':p.name,
                         'successes':report['successes'],'valid_flights':report['valid_flights'],
                         'first_touch_precise':report['first_touch_precise_episodes'],'stabilized':report['stabilized_episodes'],
                         'by_distance':report['by_distance']})
    out={'rows':rows,'policy_stds':stds,'additional_training_steps':0,
         'scope':'Frozen policy mean versus two independent Gaussian RNG repeats on identical scenarios; not proof that changing exploration improves training.'}
    (ROOT/'docs/p2-19-summary.json').write_text(json.dumps(out,indent=2)+'\n')
    lines=['# P2-19 행동 샘플링 진단','', '평균 행동 결과는 기존 P2-18의 모든 episode 결과와 일치했다. 동일 checkpoint·초기조건·목표 목록에서 샘플링 여부만 바꿨다. 추가 학습0step.', '',
           '| 학습 seed | 행동 모드 | 행동 RNG | 성공 /64 | 유효 비행 | 첫 접촉 정밀 | 안정화 |','|---|---|---:|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['seed']} | {r['mode']} | {r['rng']} | {r['successes']} | {r['valid_flights']} | {r['first_touch_precise']} | {r['stabilized']} |")
    lines+=['','환경 행동 스케일 적용 전 정책 출력 단위에서 관절별 표준편차 평균: '+', '.join(f"seed{s['seed']}={s['mean_std']:.4f}" for s in stds)+'.', '',
            '샘플링 두 반복은 별도 학습 seed가 아니다. 평가의 normalization은 고정이며 PPO 업데이트·정규화 갱신·훈련 목표 분포를 재현한 실험이 아니다. 탐색을 줄인 학습이 개선된다는 결론에는 별도 고정 예산 비교가 필요하다.','']
    (ROOT/'docs/p2-19-results.md').write_text('\n'.join(lines));print('\n'.join(lines))
if __name__=='__main__':main()
