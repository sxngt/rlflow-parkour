# P2-18 · 비행 이동과 최초 접촉 결합 보상

거리 가중치12 단독 조건과 최초 네 발 접촉 결합 조건을 동일 예산으로 비교한다. 기존 P2-17 결과는 재사용 대조군이다.

고유 학습 run 기준 314,572,800 환경 step, 신규 157,286,400step. [사전 프로토콜](p2-18-protocol.md).

| 발 | 조건 | seed | 목표 도약 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GROUP | distance-only12 | 0 | 0/64 | 64/64 | 0/64 | 64/64 | 64/64 |
| GROUP | distance-only12 | 1 | 0/64 | 64/64 | 0/64 | 64/64 | 64/64 |
| GROUP | distance-only12 | 2 | 3/64 | 64/64 | 0/64 | 61/64 | 64/64 |
| GROUP | distance-only12 | 3 | 0/64 | 64/64 | 0/64 | 64/64 | 64/64 |
| GROUP | coupled-first-touch12 | 0 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |
| GROUP | coupled-first-touch12 | 1 | 0/64 | 64/64 | 0/64 | 64/64 | 64/64 |
| GROUP | coupled-first-touch12 | 2 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |
| GROUP | coupled-first-touch12 | 3 | 33/64 | 64/64 | 0/64 | 31/64 | 64/64 |

## 도약 계약 지표

| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 목표 도약 성공 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| distance-only12 | 0 | 64/64 | 64/64 | 0/64 | 0 | 9.09 cm | 64/64 | 16/64 | 0/64 |
| distance-only12 | 1 | 64/64 | 64/64 | 0/64 | 0 | 10.24 cm | 64/64 | 15/64 | 0/64 |
| distance-only12 | 2 | 64/64 | 64/64 | 3/64 | 0 | 10.21 cm | 64/64 | 4/64 | 0/64 |
| distance-only12 | 3 | 64/64 | 64/64 | 0/64 | 0 | 8.93 cm | 64/64 | 32/64 | 0/64 |
| coupled-first-touch12 | 0 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 0/64 |
| coupled-first-touch12 | 1 | 64/64 | 64/64 | 0/64 | 0 | 7.47 cm | 64/64 | 49/64 | 0/64 |
| coupled-first-touch12 | 2 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 0/64 |
| coupled-first-touch12 | 3 | 64/64 | 64/64 | 33/64 | 0 | 8.78 cm | 64/64 | 64/64 | 0/64 |

## 발별 첫 접촉

오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.

| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |
|---|---:|---|---:|---:|---:|
| distance-only12 | 0 | FL | 64/64 | 4.72 cm | 46/64 |
| distance-only12 | 0 | FR | 64/64 | 2.76 cm | 55/64 |
| distance-only12 | 0 | RL | 64/64 | 5.21 cm | 32/64 |
| distance-only12 | 0 | RR | 64/64 | 5.40 cm | 16/64 |
| distance-only12 | 1 | FL | 64/64 | 4.05 cm | 47/64 |
| distance-only12 | 1 | FR | 64/64 | 3.60 cm | 48/64 |
| distance-only12 | 1 | RL | 64/64 | 6.63 cm | 15/64 |
| distance-only12 | 1 | RR | 64/64 | 5.05 cm | 37/64 |
| distance-only12 | 2 | FL | 64/64 | 3.62 cm | 46/64 |
| distance-only12 | 2 | FR | 64/64 | 5.47 cm | 22/64 |
| distance-only12 | 2 | RL | 64/64 | 4.37 cm | 43/64 |
| distance-only12 | 2 | RR | 64/64 | 5.28 cm | 22/64 |
| distance-only12 | 3 | FL | 64/64 | 3.50 cm | 46/64 |
| distance-only12 | 3 | FR | 64/64 | 2.98 cm | 64/64 |
| distance-only12 | 3 | RL | 64/64 | 5.15 cm | 40/64 |
| distance-only12 | 3 | RR | 64/64 | 2.67 cm | 64/64 |
| coupled-first-touch12 | 0 | FL | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 0 | FR | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 0 | RL | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 0 | RR | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 1 | FL | 64/64 | 2.63 cm | 64/64 |
| coupled-first-touch12 | 1 | FR | 64/64 | 3.37 cm | 58/64 |
| coupled-first-touch12 | 1 | RL | 64/64 | 2.43 cm | 63/64 |
| coupled-first-touch12 | 1 | RR | 64/64 | 3.69 cm | 51/64 |
| coupled-first-touch12 | 2 | FL | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 2 | FR | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 2 | RL | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 2 | RR | 0/64 | N/A | 0/64 |
| coupled-first-touch12 | 3 | FL | 64/64 | 2.59 cm | 64/64 |
| coupled-first-touch12 | 3 | FR | 64/64 | 0.75 cm | 64/64 |
| coupled-first-touch12 | 3 | RL | 64/64 | 2.24 cm | 64/64 |
| coupled-first-touch12 | 3 | RR | 64/64 | 2.33 cm | 64/64 |

## 공통 지표 분리

| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |
|---|---:|---:|---:|
| distance-only12 | 0 | 0/64 | 16/64 |
| distance-only12 | 1 | 0/64 | 15/64 |
| distance-only12 | 2 | 30/64 | 4/64 |
| distance-only12 | 3 | 0/64 | 32/64 |
| coupled-first-touch12 | 0 | 0/64 | 0/64 |
| coupled-first-touch12 | 1 | 0/64 | 49/64 |
| coupled-first-touch12 | 2 | 0/64 | 0/64 |
| coupled-first-touch12 | 3 | 47/64 | 64/64 |

## 출발 계약과 궤적 부분집합

3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.

| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |
|---|---:|---:|---:|---:|
| distance-only12 | 0 | 3 cm | 64/64 | 0/64 |
| distance-only12 | 1 | 3 cm | 64/64 | 0/64 |
| distance-only12 | 2 | 3 cm | 64/64 | 3/64 |
| distance-only12 | 3 | 3 cm | 64/64 | 0/64 |
| coupled-first-touch12 | 0 | 3 cm | 0/64 | 0/64 |
| coupled-first-touch12 | 1 | 3 cm | 64/64 | 0/64 |
| coupled-first-touch12 | 2 | 3 cm | 0/64 | 0/64 |
| coupled-first-touch12 | 3 | 3 cm | 64/64 | 33/64 |

## 거리별 평가

| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |
|---|---:|---:|---:|---:|---:|---:|---:|
| distance-only12 | 0 | 0 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 0 | 5 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 0 | 10 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| distance-only12 | 0 | 15 cm | 0/16 | 16/16 | 2/16 | 0/16 | 0/16 |
| distance-only12 | 1 | 0 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 1 | 5 cm | 0/16 | 16/16 | 16/16 | 15/16 | 0/16 |
| distance-only12 | 1 | 10 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 1 | 15 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 2 | 0 cm | 0/16 | 16/16 | 16/16 | 0/16 | 5/16 |
| distance-only12 | 2 | 5 cm | 3/16 | 16/16 | 16/16 | 4/16 | 8/16 |
| distance-only12 | 2 | 10 cm | 0/16 | 16/16 | 16/16 | 0/16 | 11/16 |
| distance-only12 | 2 | 15 cm | 0/16 | 16/16 | 16/16 | 0/16 | 6/16 |
| distance-only12 | 3 | 0 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 3 | 5 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-only12 | 3 | 10 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| distance-only12 | 3 | 15 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| coupled-first-touch12 | 0 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 0 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 0 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 0 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 1 | 0 cm | 0/16 | 16/16 | 16/16 | 10/16 | 0/16 |
| coupled-first-touch12 | 1 | 5 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| coupled-first-touch12 | 1 | 10 cm | 0/16 | 16/16 | 0/16 | 16/16 | 0/16 |
| coupled-first-touch12 | 1 | 15 cm | 0/16 | 16/16 | 0/16 | 7/16 | 0/16 |
| coupled-first-touch12 | 2 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 2 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 2 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 2 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| coupled-first-touch12 | 3 | 0 cm | 3/16 | 16/16 | 16/16 | 16/16 | 3/16 |
| coupled-first-touch12 | 3 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| coupled-first-touch12 | 3 | 10 cm | 14/16 | 16/16 | 16/16 | 16/16 | 14/16 |
| coupled-first-touch12 | 3 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 14/16 |

![학습 곡선](figures/p2-18-learning.png)

학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.

## 종료 단계

- GROUP distance-only12 seed 0: `{'2:2': 64}`
- GROUP distance-only12 seed 1: `{'2:2': 64}`
- GROUP distance-only12 seed 2: `{'2:2': 64}`
- GROUP distance-only12 seed 3: `{'2:2': 64}`
- GROUP coupled-first-touch12 seed 0: `{'0:0': 64}`
- GROUP coupled-first-touch12 seed 1: `{'2:2': 64}`
- GROUP coupled-first-touch12 seed 2: `{'0:0': 64}`
- GROUP coupled-first-touch12 seed 3: `{'2:2': 64}`

## 마지막 제어 표본의 안정화 조건 위반

복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.

- distance-only12 seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 64, 'contact_state': 32, 'support_history': 58}`
- distance-only12 seed 1: `{'height': 0, 'vertical_speed': 7, 'angular_speed': 49, 'foot_target': 64, 'contact_state': 47, 'support_history': 63}`
- distance-only12 seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 6, 'foot_target': 42, 'contact_state': 3, 'support_history': 7}`
- distance-only12 seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 27, 'foot_target': 48, 'contact_state': 31, 'support_history': 57}`
- coupled-first-touch12 seed 0: `{'height': 0, 'vertical_speed': 64, 'angular_speed': 0, 'foot_target': 64, 'contact_state': 64, 'support_history': 64}`
- coupled-first-touch12 seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 31, 'foot_target': 60, 'contact_state': 45, 'support_history': 62}`
- coupled-first-touch12 seed 2: `{'height': 0, 'vertical_speed': 64, 'angular_speed': 19, 'foot_target': 64, 'contact_state': 64, 'support_history': 64}`
- coupled-first-touch12 seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 17, 'contact_state': 0, 'support_history': 0}`

## 해석 및 다음 판단

분석 중. 표만으로 모델 승격을 결정하지 않는다.

## 범위·재현

개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종 병렬 평가 영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.

실행 목록 및 보고서 명세: `configs/reports/p2-18.json`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다.
