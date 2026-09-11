# 현재 연구 인계

2026-09-12 갱신. 실제 worker·GPU 및 artifact로 상태를 다시 확인한다. 사용자가 중단할 때까지 연구 goal은 active다.

## 현재 작업: P2-06 학습 거리 범위

[P2-06 사전 프로토콜](p2-06-protocol.md). DirectedJumpEnv와 보상·성공 기준을 유지하고 학습 거리만 제자리 / 0–5cm로 비교한다. 각 조건 seed0/1, 각각1024환경 ×24step ×1600updates. 총157,286,400 신규step. 네 run 모두 신규 학습이다.

| GPU | 실행 | shell session |
|---|---|---|
| 0 | p2-06-zero-seed0 | 42659 |
| 1 | p2-06-zero-seed1 | 61387 |
| 2 | p2-06-short-seed0 | 15729 |
| 3 | p2-06-short-seed1 | 59082 |

학습 source commit c3f094b. 각 supervisor 제한3600초, 종료 후64개 고정 평가·200Hz 진단·16대 MP4가 자동 실행된다. 실제 PID와 step 증가를 확인하고 중복 실행하지 않는다. 평가 거리는0/5/10/15cm 각각16개로 유지한다. 학습 범위 밖 거리는 전이 진단으로 분리한다.

## 직전 결과: P2-05

[결과](p2-05-results.md). 4개 seed 모두0/64 성공. seed1은 유효 비행·출발 영역64/64, 첫 접촉 정밀1/64, 안정화0/64. 나머지는 유효 비행0/64다. 모두 timeout이며 출발 영역 위반 종료가 아니다. 20ms 전 발 무접촉은 모두64/64지만 유효 비행의 상승 높이·속도 조건과 구분해야 한다.

원본200Hz 첫 접촉 및 launch/first-touch root XY 대조 통과. 학습4개·평가4개 audit 통과, artifacts/p2-05-audit.jsonl. result/에 상세 제목의 평가 영상4개 보존. 종료 후 GPU compute PID가 없음을 확인했다. 모델 승격 없음.

P2-04는 동일 초기 자세·평지 제자리 정밀 도약을 네 seed 각각64/64 성공했다. P2-05 실패로 수평 목표 일반화는 아직 달성하지 못했다. P1 정적 발 디딤의 재현성 한계도 해결했다고 표현하지 않는다.

## 완료 후

1. 실제 worker 종료·GPU 회수 및8개 run 감사.
2. Isaac Python으로 scripts/experiment_report.py configs/reports/p2-06.json 및 scripts/jump_trace_report.py configs/reports/p2-06.json 실행.
3. 거리별 유효 비행·출발·실제 이동·첫 접촉·안정화 분리. 원본 기록 대조 assertion이 실패하면 원인을 조사한다.
4. zero의0cm, short의0/5cm 결과를 먼저 판정한다. 두 seed의 탐색적 비교이며 효과를 확정하지 않는다.
5. 결과에 따라 커리큘럼/전이 또는 출발·비행 보상 계약 진단을 고정 예산으로 설계하고 지속한다. result/영상·모니터링 태그·인계 갱신, 자동 승격 없음.

## 환경

Isaac Python: /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. .monitor-venv에는 NumPy가 없다. 모니터링 http://203.241.249.48:18710/ . 새 phase/step/condition 태그는 configs/research-tags.json에 등록됐다. 전체 이력은 [p0-status.md](p0-status.md).

추가 원인 분석: [P2-05 비행 조건 진단](p2-05-flight-diagnosis.md). 세 실패 seed는50Hz 경계 최대 상승이1.55–2.80cm로3cm 기준 미달이다. 20ms 공중 이력과 양의 상승속도는 관측됐다. scripts/flight_gate_report.py로 원본200Hz에서 재생성 가능하며 실패/출발 조건 전체를 재구성하는 도구는 아니다.
