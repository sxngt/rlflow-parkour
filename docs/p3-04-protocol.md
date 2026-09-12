# P3-04 실제 코스 학습과 deck 대조

목표: 동일 부모 모델/계산 예산에서 실제 불연속 코스 학습이 course 재도약을 개선하는지 검증한다. P240 seed1/2 checkpoint800을 각각 부모로 사용한다. 두 seed는 기존 실행능력을 근거로 선택한 개발 대상이며 모집단 전체 안정성 주장이 아니다.

조건A:12패드 course. 조건B:기존 deck. 두 조건 모두 homogeneous 두hop,hold-last준비명령,schema2 chain 계약,15cm/hop,4초/hop이다. 기존 mixed single/chain에서 새실험으로fork:policy/critic/normalizer복사,optimizer/RNG/curriculum새시작. 보상/관측/PD/성공판정/timeout처리는유지한다. 실험간 차이는terrain mode/layout만. 각1024env×24step×800update=19,660,800step,2조건×2seed총78,643,200step. 시작 전64env12update+2update resume로계약/저장/재개/native최종평가를검증하고1024env60update로비용측정한다. 이 smoke/profile은본예산과별도기록,부모모델로사용하지않는다.

평가:각후보 course/hold-last64개와 deck64개,continuous단일0/5/10/15cm64개를고정시나리오에서평가한다. 부모와동일계약평가를확보해전후/대조를비교한다. 전체완주,첫/두번째도약,회귀성능,200Hz진단을보고한다.64로봇camera4영상/result상세제목/phase:P3/step:p3-04-course-training태그. 아직지도계획은같은고정경로이므로학습과정에계획탐색을중복하지않는다. 자동champion승격없음.800update종료후실패조건에따라결정하고무한sweep하지않는다.
