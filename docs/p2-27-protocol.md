# P2-27 좁은 연속 지지면 직접 학습

P2-26의갭없는continuous에서도준비중실패한문제를검증한다. P2-24와동일한PPO/관측/보상/거리·출발반경·탐색일정으로fresh4seed를학습하되terrain만deck에서continuous로변경한다. 기존P2-24의4seed를재사용대조군으로명시한다. 관측에지도경계를추가하지않는다. 정적발별24×12cm지지면을학습분포에포함한효과를탐색하며동적폭커리큘럼은추가하지않는다.

각1024env×24step×1600update,총추가157286400step. 목표0–5/10/15cm일정및최종std.05는P224와동일. train/eval/curriculum의모든목표중심에반지름2cm발투영여유를검사한다. 성공반경5cm전체가발판내부라는뜻은아니므로성공과실제표면투영포함을별도보고한다. 발판geometry와보정값은P226continuous와동일. 평면z−.5m,마찰.5/.5/rest0,기존구동기·실패판정유지.

본학습전58unit검증,64env3update축소일정smoke(거리와반경·std전환),checkpoint재개,zero action지지probe를수행한다. smoke는학습성공근거가아니다. 기존artifact덮어쓰기금지. train과eval의실제terrain/collision계약을감사한다.

주요평가: 각모델continuous와deck에서동일0/5/10/15cm×16 높이명령64episode,현재고정평가와동일seed. 넓은발판기존능력은fresh정책의교차지형성능으로표현하며기존가중치의망각이라고표현하지않는다. P224동결정책도동일continuous에서추가평가하여학습지형효과를비교한다. split전이는후속진단. 실패seed교체/예산연장/판정완화없음.

각실행checkpoint·200Hz·64env/camera4영상·result상세제목·phase:P2/step:p2-27-support-training 태그. 기존15cm고정전이군과혼합거리군을구분한다. 주요학습전환401/801/1201과최종artifact감사. 모든seed실패시좁은지지면적응을달성했다고주장하지않고준비동작/보상도달성/지도관측필요성을분석한다.

실행 순서 보충: seed2의 학습 전 초기화 정체로 나머지 seed가 먼저 완료될 경우, 완료된 seed의 교차 평가를 먼저 실행할 수 있다. 최종 분석의 네 seed 요구·시나리오·예산은 유지한다. 이는 성능 기준 선별이 아니라 자원 사용 순서 변경이며 미완료 seed를 제외한 최종 성능 주장은 하지 않는다.
