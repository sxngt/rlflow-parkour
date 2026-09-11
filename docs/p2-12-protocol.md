# P2-12 · 동일 환경 step 예산의 병렬 규모 비교

8,192환경의 실제 동시 처리량은 GPU당 약11.4만step/s였다. 이것이 더 빠른 목표 성능 도달로 이어지는지는 아직 모른다. P2-11과 같은 총 환경step에서 정책 성능을 비교한다.

새 정책 seed0–3, 전이 없음. 각8192환경×24step×200updates=39,321,600step, 총157,286,400step. P2-11의1024×24×1600과 같다. 커리큘럼은1–100update6cm,101–150update4.5cm,151–200update3cm. 경계의 환경step과 각 조건 노출 비율을 동일하게 유지하고, 경계에서 모든 env reset한다. 8배 많은 미완료episode를 버릴 수 있다는 차이는 남는다.

PPO rollout batch는24576→196608, minibatch는6144→49152, epoch5/minibatches4는 동일, update횟수는1600→200이다. 이는 batch와 갱신 빈도 변경의 종합 효과를 비교하는 실험이다. 알고리즘이 완전히 동일한 조건이라고 표현하지 않는다. 초기화·normalization 표본 순서도 환경 수에 따라 달라진다. seed 번호를 맞추지만 episode 궤적까지 동일하지 않다.

나머지 보상·로봇·관측·행동·거리분포는P2-11과 동일. checkpoint는25update마다(총8회), worker제한1800초. 중간성공에따라예산을연장하지않는다. wall-clock은 전체실행과rollout/update구간을구분하고checkpoint횟수차이를기록한다.

최종평가는3cm출발 조건,0/5/10/15cm 각16개 고정episode,200Hz 진단과16로봇MP4. 각seed 성공·비행·첫접촉·안정화 및학습시간을P2-11과비교한다. trace는episode3. result에상세제목보존,phase:P2 및step:p2-12-large-batch 태그. 짧은profiling 정책의성과와섞지않는다.

P2-11 기준성공48/17/51/51(out of64). P2-12에서성능이낮으면처리량만근거로8192를기본값으로채택하지않는다. 4096 절충규모 또는minibatch 갱신구조는별도후속가설로검토한다. 실제갭/발판/Planner로이어갈원래연구범위를유지한다.
