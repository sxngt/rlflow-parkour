# P2-23 제한 탐색 정책의 평균 행동과 샘플링 행동 진단

P2-22 일부seed의 마지막 훈련구간 성공빈도와 최종평균행동 평가가 크게 달랐다. 정책·목표분포·행동샘플링을 동시에 바꿔 해석하지 않고 고정모델·고정개발군에서 행동 선택만 비교한다.

P2-20/P2-22 각각seed0–3의최종1600update checkpoint를 사용한다. mean결과8개는 이미 감사한 최종평가를 재사용한다. 각모델에 sampled행동RNG20000/20001을 적용해새평가16개를 수행한다. 추가학습0step. 각평가는같은64개scenario이며 model/normalization은고정한다. RNG반복을독립학습seed로취급하지않는다.

기존sample_action은PPO update_distribution의평균/표준편차를사용하고 독립torch.Generator에서매step 전체행의잡음을생성한다. bounded모델은checkpoint의std_floor/std_cap buffer를복원한clamp분포를사용한다. 최종cap0.1을확인하고 rawstd를실제행동표준편차로보고하지않는다. 학습시나리오 RNG 또는 정책업데이트를재현한실험은아니다.

평가당240초/GPU당1개, seed별P2-20 두RNG→P2-22 두RNG 순서로실행한다. 기존성공판정/동결초기상태/지형/거리0·5·10·15cm를유지한다. 200Hz진단·64개렌더링/camera_side4·상세제목result영상과phase:P2/step:p2-23-bounded-action-sampling/action:sampled태그를남긴다.

모든16개감사와scenario동일성/checkpoint hash/행동mode·RNG/설정동일성/effective std를검증한후 seed별성공·비행·최초정밀·안정화·거리별결과를보고한다. 샘플링이유리해도기존mean평가를대체하거나champion으로승격하지않는다. 학습성공과의차이가모두잡음때문이라고결론내리지않는다.
