# 현재 연구 인계

2026-09-12 갱신. 사용자 중단 전까지 연구 goal active. 실제 PID·GPU·artifact로 상태를 재확인한다.

## 현재 작업: P2-07 출발 영역 진단

[사전 프로토콜](p2-07-protocol.md). P2-06과 동일한 설정에서 출발 반경만3→6cm로 변경했다. config 비교로 태그 외 다른 차이가 없음을 확인했다. source commit1cb2cf0. 각1024환경×24step×1600updates, 총157,286,400 신규step. 신규 정책 학습이며 전이 없음.

| GPU | 실행 | shell session |
|---|---|---|
| 0 | p2-07-zero-seed0 | 53438 |
| 1 | p2-07-zero-seed1 | 26781 |
| 2 | p2-07-short-seed0 | 65499 |
| 3 | p2-07-short-seed1 | 52191 |

zero는 제자리, short는0–5cm 학습. worker 제한3600초, 자동64개 고정 평가·16대 MP4·200Hz 진단. 평가0/5/10/15cm 각각16개, 범위 밖 명령은 전이 진단이다. 실행 도중 설정 변경·중복 실행 금지. PID는 새 턴에서 확인한다.

## 직전 결과

[P2-06 결과](p2-06-results.md): 네 실행 모두 유효 비행0/64, 성공0/64. 50Hz 제어 경계의 최대 상승1.26–2.46cm로3cm 비행 조건 미달. 원본 전체 기록은 p2-06-flight-gates.json. 학습4개·평가4개 감사 통과(artifacts/p2-06-audit.jsonl), GPU compute PID 없음 확인, result/평가영상4개 보존. 학습 거리 범위만 줄여서는 회복되지 않았다.

[P2-05](p2-05-results.md)는0–15cm 학습 네 seed 모두 성공0/64. seed1만 유효 비행·출발 영역64/64, 첫 접촉 정밀1/64, 안정화0/64. 세 seed 최대 상승1.55–2.80cm.

[P2-04 출발 위치 사후 진단](p2-04-launch-region-retrospective.md): 기존 성공 정책은 비행 확인 시 몸체 이동4.18–5.06cm로3cm 출발 영역을 모두 벗어났다. P2-04의 원래 성공 기준은 유지하며 새로운 제약을 만족한 것으로 간주하지 않는다. P2-05 seed1은3cm 안에서 유효 비행을 했으므로 불가능한 조건이라고도 단정하지 않는다.

## 완료 후 필수 절차

1. 실제 worker 종료·GPU 회수와8개 run 감사.
2. Isaac Python으로 scripts/experiment_report.py configs/reports/p2-07.json 및 scripts/jump_trace_report.py configs/reports/p2-07.json.
3. scripts/flight_gate_report.py로 원본 비행 조건 보조 진단. 이 도구는 failure·already-seen·출발 제약을 모두 복원하는 것이 아니다.
4. 원본 첫 접촉/launch/first-touch root 좌표 대조.6cm 성공 중 보정 출발점으로부터3cm 내 launch인 부분집합을 별도 집계. 이는3cm 종료 조건으로 재실행한 평가를 대체하지 않는다. 성공 기준 완화를 동일 기준 성능 개선이라고 표현하지 않는다.
5. 조건별0cm/5cm 평가를 우선하며 두 seed 탐색적 비교라는 한계를 남긴다. 결과에 따라 수평 이동·실제 지지면 도입 또는 비행 전 보상 유인을 조사한다. 모델 자동 승격 없음.
6. 상세 제목 result/영상·웹 태그·README·본 인계 갱신. P2-06과P2-07 성공률은 계약이 다르므로 그대로 합치지 않는다.

## 환경

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. .monitor-venv에는 NumPy 없음. 모니터링 http://203.241.249.48:18710/ . 단계·조건 태그 configs/research-tags.json. 장기 이력 [p0-status.md](p0-status.md). 실기·실제 갭·Planner는 아직 검증하지 않았다.
