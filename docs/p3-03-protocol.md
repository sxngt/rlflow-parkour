# P3-03 지도 기반 기하학적 Planner 연결

수평 표면 중심에서 후보 평행이동을 생성한다. 초기 네 발 상대 배치를 유지하며 네 개의 서로 다른 표면에2cm여유로 들어가는 후보만 남긴다. 발 이름/role/landing_targets 라벨은 선택에 사용하지 않는다. 전방4~16cm 연결, 최대2hop의 graph search로 목적지30cm에 도달하는 경로를 선택한다. 현재 물리 실행 어댑터는15cm씩2hop만 지원하므로 다른 경로는 명시적으로 기각한다. body swept-volume/동역학/rollout 검증은 아직 없다.

P240 seed1/800고정, P3-02 hold-last,64개 개발조건,동일course,새학습0step. Planner 결과를 최초 목표와 다음 도약 목표에 전달한다. geometric-plan.json에 후보/기각/표면ID/목표/계산시간 기록 및hash. 이번 지도에서 수동경로와 동일경로가 선택되므로 첫episode 결과와motion trace를 P3-02와 비교한다. 성능 개선실험이 아니라 지도→계획→Tracker 통합 검증이며 기존0/64 실패를 숨기지 않는다. phase:P3/step:p3-03-geometric-planner. 64로봇camera4영상/200Hz진단/result보관.
