# P3-03 지도→계획→Tracker 통합 결과

수평 전방 평행이동에 한정한 geometric_planner가 course의 실제 표면 bounds/centers를 읽고15cm→30cm 경로를 선택했다. 기존 수동 목표 입력을 이 계획으로 대체하여 최초 목표와 다음 도약 목표에 전달했다. 역할/발이름 라벨과 landing_targets를 지운 테스트에서도 경로를 찾고, 지도 station을10/20cm로 옮긴 테스트에서는10/20cm경로를 선택한다. 누락된 착지면,도달범위 부족,margin 부족,hop예산 부족은 no_plan으로 처리한다.4개 단위시험 통과.

고정모델64episode 시뮬레이션 정상완료. P3-02와 전episode 결과/모든200Hz motion trace 배열이 정확히 일치한다. 완주0/64이며 첫도약51개 성공. 동일 경로에서 계획 연결이 실행을 바꾸지 않았다는 검증이고 제어성능 개선은 아니다. docs/p3-03-audit.json에 검증결과. plan/artifact/보관영상hash검증,준비명령/물리상태보존 감사통과. result/2026-09-12__A1__T1J-v5__seed-1__updates-000800__p3-03-map-plan-seed1 에 영상등록. phase:P3/step:p3-03-geometric-planner 태그.

이번 계획 계산은약0.13ms 단1회 측정으로 latency 성능주장은 아니다. 현재 Tracker 어댑터는15cm씩2hop만 지원하여 다른 계획은 실행 전에 기각한다. 몸체 swept-volume,기울어진 면,방향전환,동역학 rollout,실행중 재계획은 미구현이다. 따라서P3 전체 완료로 표시하지 않는다.

## 인계

추가 보상 sweep 대신 실제 course 실행을 우선한다. 기존hold-last는준비중즉시충돌은없앴지만 다음 비행의출발영역조건과동작실패는남았다. 다음은현재착지상태/발판위지지여유와launch관측을 대조해 실제코스에서재도약을학습하는명세를 작성하고,연속course분포를실행기학습에연결한다. 계획경로를선택했다고실행가능하다고간주하지않는다. 물리rollout 검증은이후Planner 비교군으로연결한다. 원본기록/artifacts보존,이번학습0step,worker종료/자원해제확인.
