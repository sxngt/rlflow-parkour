# P2-26 현재 정책의 실제 지지면 전이 진단

P2-25의 네 seed 최종1600 checkpoint를 모두 동결한다. 추가학습0step. 동일15cm 목표·64개 높이 명령을 deck/continuous/split에 짝지어 평가한다. 각 seed3조건, 총12개 평가768episode. 좋은 seed만 선별하지 않는다. P2-25의 혼합거리 평가64개와 본 평가의15cm64개는 서로 다른 평가군이다.

기존 calibration(P2-11 seed0 최종평가)이 현재 학습 terrain 계약의 calibration과 정확히 일치함을 착수 시 대조했다. config와 checkpoint restore 계약은 유지하고 명시적 evaluation support만 바꾼다. matched material(마찰.5/.5, restitution0), 동일로봇·PD·접촉·종료·정규화·mean action을 유지한다. 새로운 물리 구현은 추가하지 않는다.

발판 geometry는 기존검증된 generator 사용: deck1.4×1.2m, continuous 발별24×12cm, split 발별출발/착지9×12cm 및실제빈공간6cm. 포획평면z=-.5m. 전신15cm 갭 도약으로 표현하지 않는다. 좁은연속지지면은 갭 없는 대조군이다. 목표면은15cm 고정이며 모든환경의 지형과명령을일치시킨다.

GPU당한seed를배정하고 deck→continuous→split 순차실행,각240초제한. 기존run/artifact존재시재실행금지. 먼저seed0 deck평가로현재계약복원과시나리오/물리manifest를확인한뒤나머지를시작한다. 첫평가도본12개에포함하며반복하지않는다.

각평가200Hz원본진단·checkpoint hash·terrain/collision manifest·64개렌더링/camera_side4·상세제목result영상·phase:P2/step:p2-26-support-transfer 태그를남긴다. 종료후12artifact감사,pairedscenario/checkpoint/calibration대조 및원본최초접촉오차대조를수행한다.

보고: seed별성공/유효비행/낙상/timeout/최초정밀/안정화와발판투영포함. 실패시준비구간의지지영역이탈과비행후실패를200Hz기록으로구분한다. 투영포함은접촉쌍의확정이나지속지지보장이아니다. 실패를제외하거나성공판정을완화하지않는다. 현재개발분포의전이진단이며최종시험/실기/연속코스성공주장금지.
