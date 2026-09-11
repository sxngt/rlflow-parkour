# P2-20 탐색 표준편차 제한

P2-19에서 같은 seed3 모델의 mean평가33/64 성공이 sampled 두반복에서는0/64였다. 비행은유지됐으나접촉정밀도와안정화가악화했다. 이는현재정책에행동잡음이주는영향이며탐색감소학습의효과는아직검증하지않았다.

P2-18과같은결합보상/거리커리큘럼/로봇/지형/관측/초기calibration/행동스케일/PPO를유지하고 실제Gaussian의관절별std에하한0.05와상한일정을적용한다. update1–800 상한0.35,801–1200 상한0.20,1201–1600 상한0.10. 초기std0.35는기존과같고평균행동으로탐색을제거하지않는다. 검증할단일일정이며최적값주장이아니다.

BoundedActorCritic.update_distribution에서학습가능한raw std를clamp해분포를구성한다. rollout샘플링/logprob/entropy/학습중새분포가같은구현을사용한다. 상한은새rollout직전update경계에서만변경하고PPO내부미니배치에서는고정한다. 범위밖raw std의clamp미분은0이며이학습효과도개입의일부다. 단순실행시행동잡음만줄이는것이아니다.

cap/floor buffer는checkpoint에저장하고평가시그대로복원한다. resume는다음rollout의절대update일정으로cap을결정한다. exploration config가다르면strictrestore를거부한다. 기존config는기존ActorCritic그대로사용한다. effective std min/max/mean/cap을update별metric에기록한다.

fresh seed0–3,각1024환경×24step×1600update=39,321,600step,총추가157,286,400step. 동일예산P2-18 네seed를재사용대조로둔다. 성공판정/목표거리/출발반경일정은변경하지않는다. rawreturn뿐아니라훈련중완전성공빈도·도약습득·최종mean평가의거리별성공/접촉/안정화를보고한다. 성능향상과도약탐색상실을함께검사한다.

주요실행전단위검사와짧은학습의축소일정전환/재개/최종평가를검증한다. 최종64개개발episode·200Hz진단·64개근접구도영상/result·phase:P2/step:p2-20-bounded-exploration. 예산임의연장·실패seed교체·성공기준완화는하지않는다. 연속파쿠르/Planner완료를주장하지않는다.
