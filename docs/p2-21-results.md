# P2-21 · 후반 학습 거리 상한 확장

제한 탐색과 결합 보상은 유지하며 후반 목표 거리 상한 15cm와20cm를 동일 예산으로 비교한다. P2-20 결과를 대조로 재사용한다.

고유 학습 run 기준 314,572,800 환경 step, 신규 157,286,400step. [사전 프로토콜](p2-21-protocol.md).

| 발 | 조건 | seed | 목표 도약 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GROUP | train-upper-15cm | 0 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | train-upper-15cm | 1 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | train-upper-15cm | 2 | 24/64 | 64/64 | 0/64 | 40/64 | 64/64 |
| GROUP | train-upper-15cm | 3 | 22/64 | 64/64 | 0/64 | 42/64 | 64/64 |
| GROUP | train-upper-20cm | 0 | 0/64 | 64/64 | 0/64 | 64/64 | 64/64 |
| GROUP | train-upper-20cm | 1 | 12/64 | 64/64 | 0/64 | 52/64 | 64/64 |
| GROUP | train-upper-20cm | 2 | 44/64 | 64/64 | 0/64 | 20/64 | 64/64 |
| GROUP | train-upper-20cm | 3 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |

## 도약 계약 지표

| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 목표 도약 성공 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| train-upper-15cm | 0 | 64/64 | 64/64 | 48/64 | 0 | 10.14 cm | 64/64 | 64/64 | 0/64 |
| train-upper-15cm | 1 | 64/64 | 64/64 | 48/64 | 0 | 12.92 cm | 64/64 | 64/64 | 5/64 |
| train-upper-15cm | 2 | 64/64 | 64/64 | 24/64 | 0 | 9.15 cm | 64/64 | 64/64 | 0/64 |
| train-upper-15cm | 3 | 64/64 | 64/64 | 22/64 | 0 | 13.43 cm | 64/64 | 64/64 | 0/64 |
| train-upper-20cm | 0 | 64/64 | 64/64 | 0/64 | 0 | 9.33 cm | 64/64 | 64/64 | 0/64 |
| train-upper-20cm | 1 | 64/64 | 64/64 | 12/64 | 0 | 13.17 cm | 64/64 | 64/64 | 0/64 |
| train-upper-20cm | 2 | 64/64 | 64/64 | 44/64 | 0 | 10.10 cm | 64/64 | 64/64 | 0/64 |
| train-upper-20cm | 3 | 64/64 | 64/64 | 48/64 | 0 | 10.77 cm | 64/64 | 64/64 | 0/64 |

## 발별 첫 접촉

오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.

| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |
|---|---:|---|---:|---:|---:|
| train-upper-15cm | 0 | FL | 64/64 | 0.94 cm | 64/64 |
| train-upper-15cm | 0 | FR | 64/64 | 0.61 cm | 64/64 |
| train-upper-15cm | 0 | RL | 64/64 | 0.43 cm | 64/64 |
| train-upper-15cm | 0 | RR | 64/64 | 0.43 cm | 64/64 |
| train-upper-15cm | 1 | FL | 64/64 | 1.67 cm | 64/64 |
| train-upper-15cm | 1 | FR | 64/64 | 1.94 cm | 64/64 |
| train-upper-15cm | 1 | RL | 64/64 | 1.72 cm | 64/64 |
| train-upper-15cm | 1 | RR | 64/64 | 2.06 cm | 64/64 |
| train-upper-15cm | 2 | FL | 64/64 | 0.93 cm | 64/64 |
| train-upper-15cm | 2 | FR | 64/64 | 0.84 cm | 64/64 |
| train-upper-15cm | 2 | RL | 64/64 | 0.86 cm | 64/64 |
| train-upper-15cm | 2 | RR | 64/64 | 0.78 cm | 64/64 |
| train-upper-15cm | 3 | FL | 64/64 | 1.50 cm | 64/64 |
| train-upper-15cm | 3 | FR | 64/64 | 1.62 cm | 64/64 |
| train-upper-15cm | 3 | RL | 64/64 | 0.84 cm | 64/64 |
| train-upper-15cm | 3 | RR | 64/64 | 1.57 cm | 64/64 |
| train-upper-20cm | 0 | FL | 64/64 | 0.82 cm | 64/64 |
| train-upper-20cm | 0 | FR | 64/64 | 0.66 cm | 64/64 |
| train-upper-20cm | 0 | RL | 64/64 | 0.70 cm | 64/64 |
| train-upper-20cm | 0 | RR | 64/64 | 0.36 cm | 64/64 |
| train-upper-20cm | 1 | FL | 64/64 | 0.70 cm | 64/64 |
| train-upper-20cm | 1 | FR | 64/64 | 1.24 cm | 64/64 |
| train-upper-20cm | 1 | RL | 64/64 | 0.69 cm | 64/64 |
| train-upper-20cm | 1 | RR | 64/64 | 0.93 cm | 64/64 |
| train-upper-20cm | 2 | FL | 64/64 | 0.34 cm | 64/64 |
| train-upper-20cm | 2 | FR | 64/64 | 0.64 cm | 64/64 |
| train-upper-20cm | 2 | RL | 64/64 | 0.69 cm | 64/64 |
| train-upper-20cm | 2 | RR | 64/64 | 0.50 cm | 64/64 |
| train-upper-20cm | 3 | FL | 64/64 | 0.78 cm | 64/64 |
| train-upper-20cm | 3 | FR | 64/64 | 1.24 cm | 64/64 |
| train-upper-20cm | 3 | RL | 64/64 | 0.67 cm | 64/64 |
| train-upper-20cm | 3 | RR | 64/64 | 0.84 cm | 64/64 |

## 공통 지표 분리

| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |
|---|---:|---:|---:|
| train-upper-15cm | 0 | 64/64 | 64/64 |
| train-upper-15cm | 1 | 64/64 | 64/64 |
| train-upper-15cm | 2 | 40/64 | 64/64 |
| train-upper-15cm | 3 | 45/64 | 64/64 |
| train-upper-20cm | 0 | 0/64 | 64/64 |
| train-upper-20cm | 1 | 18/64 | 64/64 |
| train-upper-20cm | 2 | 44/64 | 64/64 |
| train-upper-20cm | 3 | 64/64 | 64/64 |

## 출발 계약과 궤적 부분집합

3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.

| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |
|---|---:|---:|---:|---:|
| train-upper-15cm | 0 | 3 cm | 64/64 | 48/64 |
| train-upper-15cm | 1 | 3 cm | 64/64 | 48/64 |
| train-upper-15cm | 2 | 3 cm | 64/64 | 24/64 |
| train-upper-15cm | 3 | 3 cm | 64/64 | 22/64 |
| train-upper-20cm | 0 | 3 cm | 64/64 | 0/64 |
| train-upper-20cm | 1 | 3 cm | 64/64 | 12/64 |
| train-upper-20cm | 2 | 3 cm | 64/64 | 44/64 |
| train-upper-20cm | 3 | 3 cm | 64/64 | 48/64 |

## 거리별 평가

| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |
|---|---:|---:|---:|---:|---:|---:|---:|
| train-upper-15cm | 0 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 0 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 0 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 0 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-upper-15cm | 1 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 1 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 1 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 1 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-upper-15cm | 2 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 2 | 5 cm | 8/16 | 16/16 | 16/16 | 16/16 | 8/16 |
| train-upper-15cm | 2 | 10 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| train-upper-15cm | 2 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-upper-15cm | 3 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-15cm | 3 | 5 cm | 6/16 | 16/16 | 16/16 | 16/16 | 6/16 |
| train-upper-15cm | 3 | 10 cm | 0/16 | 16/16 | 0/16 | 16/16 | 7/16 |
| train-upper-15cm | 3 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-upper-20cm | 0 | 0 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| train-upper-20cm | 0 | 5 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| train-upper-20cm | 0 | 10 cm | 0/16 | 16/16 | 0/16 | 16/16 | 0/16 |
| train-upper-20cm | 0 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 0/16 |
| train-upper-20cm | 1 | 0 cm | 10/16 | 16/16 | 16/16 | 16/16 | 10/16 |
| train-upper-20cm | 1 | 5 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| train-upper-20cm | 1 | 10 cm | 2/16 | 16/16 | 16/16 | 16/16 | 2/16 |
| train-upper-20cm | 1 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 6/16 |
| train-upper-20cm | 2 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-20cm | 2 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-20cm | 2 | 10 cm | 4/16 | 16/16 | 16/16 | 16/16 | 4/16 |
| train-upper-20cm | 2 | 15 cm | 8/16 | 16/16 | 16/16 | 16/16 | 8/16 |
| train-upper-20cm | 3 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-20cm | 3 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-20cm | 3 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-upper-20cm | 3 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |

![학습 곡선](figures/p2-21-learning.png)

학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.

## 종료 단계

- GROUP train-upper-15cm seed 0: `{'2:2': 64}`
- GROUP train-upper-15cm seed 1: `{'2:2': 64}`
- GROUP train-upper-15cm seed 2: `{'2:2': 64}`
- GROUP train-upper-15cm seed 3: `{'2:2': 64}`
- GROUP train-upper-20cm seed 0: `{'2:2': 64}`
- GROUP train-upper-20cm seed 1: `{'2:2': 64}`
- GROUP train-upper-20cm seed 2: `{'2:2': 64}`
- GROUP train-upper-20cm seed 3: `{'2:2': 64}`

## 마지막 제어 표본의 안정화 조건 위반

복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.

- train-upper-15cm seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- train-upper-15cm seed 1: `{'height': 5, 'vertical_speed': 12, 'angular_speed': 13, 'foot_target': 15, 'contact_state': 8, 'support_history': 9}`
- train-upper-15cm seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 24, 'contact_state': 0, 'support_history': 0}`
- train-upper-15cm seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 19, 'contact_state': 0, 'support_history': 0}`
- train-upper-20cm seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 64, 'contact_state': 0, 'support_history': 0}`
- train-upper-20cm seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 47, 'contact_state': 0, 'support_history': 0}`
- train-upper-20cm seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 20, 'contact_state': 0, 'support_history': 0}`
- train-upper-20cm seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`

## 해석 및 다음 판단

분석 중. 표만으로 모델 승격을 결정하지 않는다.

## 범위·재현

개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종 병렬 평가 영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.

실행 목록 및 보고서 명세: `configs/reports/p2-21.json`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다.
