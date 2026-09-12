# P2-30 primary

Same split parent, fixed15 versus uniform discrete0/15; seed-paired comparison; parent training reused.

고유 학습 run 기준 235,929,600 환경 step, 신규 157,286,400step. [사전 프로토콜](p2-30-protocol.md).

| 발 | 조건 | seed | 목표 도약 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GROUP | parent | 0 | 64/64 | 64/64 | 0/64 | 0/64 | 64/64 |
| GROUP | fixed | 0 | 32/64 | 32/64 | 32/64 | 0/64 | 64/64 |
| GROUP | mixed | 0 | 61/64 | 64/64 | 0/64 | 3/64 | 64/64 |
| GROUP | parent | 1 | 34/64 | 64/64 | 0/64 | 30/64 | 64/64 |
| GROUP | fixed | 1 | 32/64 | 32/64 | 9/64 | 23/64 | 38/64 |
| GROUP | mixed | 1 | 32/64 | 32/64 | 0/64 | 32/64 | 64/64 |
| GROUP | parent | 2 | 32/64 | 32/64 | 32/64 | 0/64 | 64/64 |
| GROUP | fixed | 2 | 32/64 | 32/64 | 0/64 | 32/64 | 32/64 |
| GROUP | mixed | 2 | 32/64 | 32/64 | 0/64 | 32/64 | 64/64 |
| GROUP | parent | 3 | 32/64 | 32/64 | 32/64 | 0/64 | 64/64 |
| GROUP | fixed | 3 | 32/64 | 35/64 | 28/64 | 4/64 | 64/64 |
| GROUP | mixed | 3 | 63/64 | 64/64 | 0/64 | 1/64 | 64/64 |

## 도약 계약 지표

| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 목표 도약 성공 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parent | 0 | 64/64 | 64/64 | 64/64 | 0 | 18.66 cm | 64/64 | 64/64 | 0/64 |
| fixed | 0 | 32/64 | 32/64 | 32/64 | 0 | 13.57 cm | 32/64 | 32/64 | 32/64 |
| mixed | 0 | 64/64 | 64/64 | 61/64 | 0 | 12.61 cm | 61/64 | 64/64 | 0/64 |
| parent | 1 | 64/64 | 64/64 | 34/64 | 0 | 7.12 cm | 34/64 | 64/64 | 0/64 |
| fixed | 1 | 32/64 | 32/64 | 32/64 | 9 | 5.55 cm | 32/64 | 32/64 | 0/64 |
| mixed | 1 | 32/64 | 32/64 | 32/64 | 0 | 5.27 cm | 32/64 | 32/64 | 0/64 |
| parent | 2 | 64/64 | 32/64 | 32/64 | 0 | 8.39 cm | 32/64 | 32/64 | 0/64 |
| fixed | 2 | 32/64 | 32/64 | 32/64 | 0 | 7.79 cm | 32/64 | 32/64 | 0/64 |
| mixed | 2 | 32/64 | 32/64 | 32/64 | 0 | 6.89 cm | 32/64 | 32/64 | 32/64 |
| parent | 3 | 64/64 | 32/64 | 32/64 | 0 | 8.16 cm | 35/64 | 32/64 | 0/64 |
| fixed | 3 | 36/64 | 35/64 | 32/64 | 2 | 5.85 cm | 32/64 | 35/64 | 16/64 |
| mixed | 3 | 64/64 | 64/64 | 63/64 | 0 | 9.34 cm | 63/64 | 64/64 | 0/64 |

## 발별 첫 접촉

오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.

| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |
|---|---:|---|---:|---:|---:|
| parent | 0 | FL | 64/64 | 0.33 cm | 64/64 |
| parent | 0 | FR | 64/64 | 0.72 cm | 64/64 |
| parent | 0 | RL | 64/64 | 0.31 cm | 64/64 |
| parent | 0 | RR | 64/64 | 0.45 cm | 64/64 |
| fixed | 0 | FL | 32/64 | 0.23 cm | 32/64 |
| fixed | 0 | FR | 32/64 | 0.12 cm | 32/64 |
| fixed | 0 | RL | 32/64 | 0.10 cm | 32/64 |
| fixed | 0 | RR | 32/64 | 0.30 cm | 32/64 |
| mixed | 0 | FL | 64/64 | 0.55 cm | 64/64 |
| mixed | 0 | FR | 64/64 | 0.37 cm | 64/64 |
| mixed | 0 | RL | 64/64 | 0.36 cm | 64/64 |
| mixed | 0 | RR | 64/64 | 0.55 cm | 64/64 |
| parent | 1 | FL | 64/64 | 0.87 cm | 64/64 |
| parent | 1 | FR | 64/64 | 0.51 cm | 64/64 |
| parent | 1 | RL | 64/64 | 0.95 cm | 64/64 |
| parent | 1 | RR | 64/64 | 0.59 cm | 64/64 |
| fixed | 1 | FL | 32/64 | 0.19 cm | 32/64 |
| fixed | 1 | FR | 32/64 | 0.21 cm | 32/64 |
| fixed | 1 | RL | 32/64 | 0.05 cm | 32/64 |
| fixed | 1 | RR | 32/64 | 0.14 cm | 32/64 |
| mixed | 1 | FL | 32/64 | 0.13 cm | 32/64 |
| mixed | 1 | FR | 32/64 | 0.17 cm | 32/64 |
| mixed | 1 | RL | 32/64 | 0.14 cm | 32/64 |
| mixed | 1 | RR | 32/64 | 0.20 cm | 32/64 |
| parent | 2 | FL | 32/64 | 0.10 cm | 32/64 |
| parent | 2 | FR | 32/64 | 0.09 cm | 32/64 |
| parent | 2 | RL | 32/64 | 0.05 cm | 32/64 |
| parent | 2 | RR | 32/64 | 0.13 cm | 32/64 |
| fixed | 2 | FL | 32/64 | 0.06 cm | 32/64 |
| fixed | 2 | FR | 32/64 | 0.15 cm | 32/64 |
| fixed | 2 | RL | 32/64 | 0.06 cm | 32/64 |
| fixed | 2 | RR | 32/64 | 0.10 cm | 32/64 |
| mixed | 2 | FL | 32/64 | 0.22 cm | 32/64 |
| mixed | 2 | FR | 32/64 | 0.22 cm | 32/64 |
| mixed | 2 | RL | 32/64 | 0.06 cm | 32/64 |
| mixed | 2 | RR | 32/64 | 0.24 cm | 32/64 |
| parent | 3 | FL | 32/64 | 0.20 cm | 32/64 |
| parent | 3 | FR | 32/64 | 0.15 cm | 32/64 |
| parent | 3 | RL | 32/64 | 0.32 cm | 32/64 |
| parent | 3 | RR | 32/64 | 0.20 cm | 32/64 |
| fixed | 3 | FL | 35/64 | 0.22 cm | 35/64 |
| fixed | 3 | FR | 35/64 | 0.13 cm | 35/64 |
| fixed | 3 | RL | 35/64 | 0.25 cm | 35/64 |
| fixed | 3 | RR | 35/64 | 0.19 cm | 35/64 |
| mixed | 3 | FL | 64/64 | 0.21 cm | 64/64 |
| mixed | 3 | FR | 64/64 | 0.19 cm | 64/64 |
| mixed | 3 | RL | 64/64 | 0.23 cm | 64/64 |
| mixed | 3 | RR | 64/64 | 0.34 cm | 64/64 |

## 공통 지표 분리

| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |
|---|---:|---:|---:|
| parent | 0 | 64/64 | 64/64 |
| fixed | 0 | 32/64 | 32/64 |
| mixed | 0 | 61/64 | 64/64 |
| parent | 1 | 34/64 | 64/64 |
| fixed | 1 | 32/64 | 32/64 |
| mixed | 1 | 32/64 | 32/64 |
| parent | 2 | 32/64 | 32/64 |
| fixed | 2 | 32/64 | 32/64 |
| mixed | 2 | 32/64 | 32/64 |
| parent | 3 | 32/64 | 32/64 |
| fixed | 3 | 32/64 | 35/64 |
| mixed | 3 | 63/64 | 64/64 |

## 출발 계약과 궤적 부분집합

3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.

| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |
|---|---:|---:|---:|---:|
| parent | 0 | 3 cm | 64/64 | 64/64 |
| fixed | 0 | 3 cm | 32/64 | 32/64 |
| mixed | 0 | 3 cm | 64/64 | 61/64 |
| parent | 1 | 3 cm | 64/64 | 34/64 |
| fixed | 1 | 3 cm | 32/64 | 32/64 |
| mixed | 1 | 3 cm | 32/64 | 32/64 |
| parent | 2 | 3 cm | 32/64 | 32/64 |
| fixed | 2 | 3 cm | 32/64 | 32/64 |
| mixed | 2 | 3 cm | 32/64 | 32/64 |
| parent | 3 | 3 cm | 32/64 | 32/64 |
| fixed | 3 | 3 cm | 35/64 | 32/64 |
| mixed | 3 | 3 cm | 64/64 | 63/64 |

## 거리별 평가

| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |
|---|---:|---:|---:|---:|---:|---:|---:|
| parent | 0 | 0 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| parent | 0 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| fixed | 0 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| fixed | 0 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| mixed | 0 | 0 cm | 29/32 | 32/32 | 32/32 | 32/32 | 29/32 |
| mixed | 0 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| parent | 1 | 0 cm | 2/32 | 32/32 | 32/32 | 32/32 | 2/32 |
| parent | 1 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| fixed | 1 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| fixed | 1 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| mixed | 1 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| mixed | 1 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| parent | 2 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| parent | 2 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| fixed | 2 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| fixed | 2 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| mixed | 2 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| mixed | 2 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| parent | 3 | 0 cm | 0/32 | 0/32 | 0/32 | 0/32 | 0/32 |
| parent | 3 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| fixed | 3 | 0 cm | 0/32 | 3/32 | 3/32 | 3/32 | 0/32 |
| fixed | 3 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |
| mixed | 3 | 0 cm | 31/32 | 32/32 | 32/32 | 32/32 | 31/32 |
| mixed | 3 | 15 cm | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |

![학습 곡선](figures/p2-30-primary-learning.png)

학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.

## 종료 단계

- GROUP parent seed 0: `{'2:2': 64}`
- GROUP fixed seed 0: `{'0:0': 32, '2:2': 32}`
- GROUP mixed seed 0: `{'2:2': 64}`
- GROUP parent seed 1: `{'2:2': 64}`
- GROUP fixed seed 1: `{'0:0': 32, '2:2': 32}`
- GROUP mixed seed 1: `{'0:0': 32, '2:2': 32}`
- GROUP parent seed 2: `{'0:0': 32, '2:2': 32}`
- GROUP fixed seed 2: `{'0:0': 32, '2:2': 32}`
- GROUP mixed seed 2: `{'0:0': 32, '2:2': 32}`
- GROUP parent seed 3: `{'0:0': 32, '2:2': 32}`
- GROUP fixed seed 3: `{'0:0': 29, '2:2': 35}`
- GROUP mixed seed 3: `{'2:2': 64}`

## 마지막 제어 표본의 안정화 조건 위반

복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.

- parent seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- fixed seed 0: `{'height': 32, 'vertical_speed': 32, 'angular_speed': 32, 'foot_target': 32, 'contact_state': 32, 'support_history': 32}`
- mixed seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- parent seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- fixed seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 2, 'foot_target': 24, 'contact_state': 15, 'support_history': 17}`
- mixed seed 1: `{'height': 0, 'vertical_speed': 29, 'angular_speed': 24, 'foot_target': 0, 'contact_state': 4, 'support_history': 17}`
- parent seed 2: `{'height': 0, 'vertical_speed': 32, 'angular_speed': 32, 'foot_target': 0, 'contact_state': 32, 'support_history': 32}`
- fixed seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- mixed seed 2: `{'height': 32, 'vertical_speed': 7, 'angular_speed': 31, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- parent seed 3: `{'height': 0, 'vertical_speed': 32, 'angular_speed': 32, 'foot_target': 32, 'contact_state': 32, 'support_history': 32}`
- fixed seed 3: `{'height': 16, 'vertical_speed': 29, 'angular_speed': 29, 'foot_target': 28, 'contact_state': 29, 'support_history': 29}`
- mixed seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`

## 해석 및 다음 판단

분석 중. 표만으로 모델 승격을 결정하지 않는다.

## 범위·재현

개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종 병렬 평가 영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.

실행 목록 및 보고서 명세: `configs/reports/p2-30-primary.json`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다.
