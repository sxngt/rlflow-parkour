# P3-01 불연속 코스 첫 통합

P1/P2의 모든 seed 안정화를 다음 단계의 전제조건으로 삼지 않는다. 추가 보상 sweep과 deadline bootstrap 비교는 보류하고 실제 코스에서 실행기의 한계를 확인한다.

고정 P2-40 seed1 checkpoint800을 사용한다. 새 학습 0step. 64개 개발 episode, 정책 mean, 2도약, 각 도약 4초, 기존 성공 판정과 관측/행동 계약을 유지한다. 목표는 각 발 초기 위치에서 전방 15cm, 30cm. 발별 3개 station, 총12개 패드, 크기6×12×10cm, 표면 높이0, catch floor -50cm. 기존9cm 패드는 rear 최종 station과 front 최초 station이 겹치므로6cm로 명시적으로 변경한다. 같은 발 station 사이 패드 간격9cm이며 전체 몸체가 넘는 갭 폭 주장이 아니다. 인접 발판 간 여유는 다르다.

고정된 발 디딤 순서를 실행하는 통합 평가이며 아직 Planner 평가가 아니다. seed1은 기존 성능을 근거로 선택한 개발 모델이고 일반화/모든 seed의 성능 주장이 아니다. 완주율, 완료 도약 수, 첫 실패 조건, 200Hz trace와 물리 상태 보존을 점검한다. 64로봇/camera_side4 MP4를 상세 제목으로 result에 보관하고 phase:P3 및 step:p3-01-course-integration 태그를 사용한다. 실패도 보관한다. 이후 지도 기반 기하학적 Planner를 연결한다.
