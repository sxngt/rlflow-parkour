# P2-29 · 분리 지지면 추가학습 회귀평가

부모정책을동일하게복사한4seed×2분기. 부모학습재사용과새분기step을구분하며원래초기화실패의인프라비용은별도계상한다.

고유 학습 run 기준 314,572,800 환경 step, 신규 157,286,400step. [사전 프로토콜](p2-29-protocol.md).

| 발 | 조건 | seed | 목표 도약 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GROUP | parent | 0 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | train-continuous | 0 | 64/64 | 64/64 | 0/64 | 0/64 | 64/64 |
| GROUP | train-split | 0 | 64/64 | 64/64 | 0/64 | 0/64 | 64/64 |
| GROUP | parent | 1 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | train-continuous | 1 | 48/64 | 48/64 | 4/64 | 12/64 | 64/64 |
| GROUP | train-split | 1 | 49/64 | 64/64 | 0/64 | 15/64 | 64/64 |
| GROUP | parent | 2 | 64/64 | 64/64 | 0/64 | 0/64 | 64/64 |
| GROUP | train-continuous | 2 | 48/64 | 48/64 | 16/64 | 0/64 | 64/64 |
| GROUP | train-split | 2 | 48/64 | 48/64 | 16/64 | 0/64 | 64/64 |
| GROUP | parent | 3 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | train-continuous | 3 | 48/64 | 48/64 | 16/64 | 0/64 | 64/64 |
| GROUP | train-split | 3 | 48/64 | 48/64 | 16/64 | 0/64 | 64/64 |

## 도약 계약 지표

| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 목표 도약 성공 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| parent | 0 | 64/64 | 64/64 | 48/64 | 0 | 21.74 cm | 64/64 | 64/64 | 0/64 |
| train-continuous | 0 | 64/64 | 64/64 | 64/64 | 0 | 16.12 cm | 64/64 | 64/64 | 0/64 |
| train-split | 0 | 64/64 | 64/64 | 64/64 | 0 | 20.87 cm | 64/64 | 64/64 | 0/64 |
| parent | 1 | 64/64 | 64/64 | 48/64 | 0 | 9.87 cm | 64/64 | 64/64 | 0/64 |
| train-continuous | 1 | 52/64 | 48/64 | 48/64 | 0 | 7.46 cm | 49/64 | 48/64 | 0/64 |
| train-split | 1 | 64/64 | 64/64 | 49/64 | 0 | 8.45 cm | 49/64 | 64/64 | 0/64 |
| parent | 2 | 64/64 | 64/64 | 64/64 | 0 | 10.35 cm | 64/64 | 64/64 | 0/64 |
| train-continuous | 2 | 64/64 | 48/64 | 48/64 | 0 | 7.37 cm | 48/64 | 48/64 | 0/64 |
| train-split | 2 | 64/64 | 48/64 | 48/64 | 0 | 9.81 cm | 48/64 | 48/64 | 0/64 |
| parent | 3 | 64/64 | 64/64 | 48/64 | 0 | 8.19 cm | 64/64 | 64/64 | 0/64 |
| train-continuous | 3 | 64/64 | 48/64 | 48/64 | 0 | 8.19 cm | 48/64 | 48/64 | 0/64 |
| train-split | 3 | 64/64 | 48/64 | 48/64 | 0 | 9.19 cm | 49/64 | 48/64 | 0/64 |

## 발별 첫 접촉

오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.

| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |
|---|---:|---|---:|---:|---:|
| parent | 0 | FL | 64/64 | 0.83 cm | 64/64 |
| parent | 0 | FR | 64/64 | 1.15 cm | 64/64 |
| parent | 0 | RL | 64/64 | 0.60 cm | 64/64 |
| parent | 0 | RR | 64/64 | 0.52 cm | 64/64 |
| train-continuous | 0 | FL | 64/64 | 0.74 cm | 64/64 |
| train-continuous | 0 | FR | 64/64 | 0.60 cm | 64/64 |
| train-continuous | 0 | RL | 64/64 | 0.62 cm | 64/64 |
| train-continuous | 0 | RR | 64/64 | 0.64 cm | 64/64 |
| train-split | 0 | FL | 64/64 | 0.29 cm | 64/64 |
| train-split | 0 | FR | 64/64 | 0.98 cm | 64/64 |
| train-split | 0 | RL | 64/64 | 0.54 cm | 64/64 |
| train-split | 0 | RR | 64/64 | 0.85 cm | 64/64 |
| parent | 1 | FL | 64/64 | 0.44 cm | 64/64 |
| parent | 1 | FR | 64/64 | 0.30 cm | 64/64 |
| parent | 1 | RL | 64/64 | 0.38 cm | 64/64 |
| parent | 1 | RR | 64/64 | 0.31 cm | 64/64 |
| train-continuous | 1 | FL | 48/64 | 0.86 cm | 48/64 |
| train-continuous | 1 | FR | 48/64 | 0.48 cm | 48/64 |
| train-continuous | 1 | RL | 48/64 | 0.53 cm | 48/64 |
| train-continuous | 1 | RR | 48/64 | 0.50 cm | 48/64 |
| train-split | 1 | FL | 64/64 | 0.77 cm | 64/64 |
| train-split | 1 | FR | 64/64 | 0.42 cm | 64/64 |
| train-split | 1 | RL | 64/64 | 0.84 cm | 64/64 |
| train-split | 1 | RR | 64/64 | 0.72 cm | 64/64 |
| parent | 2 | FL | 64/64 | 0.56 cm | 64/64 |
| parent | 2 | FR | 64/64 | 0.40 cm | 64/64 |
| parent | 2 | RL | 64/64 | 0.38 cm | 64/64 |
| parent | 2 | RR | 64/64 | 0.83 cm | 64/64 |
| train-continuous | 2 | FL | 48/64 | 0.69 cm | 48/64 |
| train-continuous | 2 | FR | 48/64 | 0.46 cm | 48/64 |
| train-continuous | 2 | RL | 48/64 | 0.44 cm | 48/64 |
| train-continuous | 2 | RR | 48/64 | 0.41 cm | 48/64 |
| train-split | 2 | FL | 48/64 | 0.49 cm | 48/64 |
| train-split | 2 | FR | 48/64 | 0.57 cm | 48/64 |
| train-split | 2 | RL | 48/64 | 0.40 cm | 48/64 |
| train-split | 2 | RR | 48/64 | 0.18 cm | 48/64 |
| parent | 3 | FL | 64/64 | 0.45 cm | 64/64 |
| parent | 3 | FR | 64/64 | 0.29 cm | 64/64 |
| parent | 3 | RL | 64/64 | 0.62 cm | 64/64 |
| parent | 3 | RR | 64/64 | 0.33 cm | 64/64 |
| train-continuous | 3 | FL | 48/64 | 1.65 cm | 48/64 |
| train-continuous | 3 | FR | 48/64 | 1.58 cm | 48/64 |
| train-continuous | 3 | RL | 48/64 | 1.84 cm | 48/64 |
| train-continuous | 3 | RR | 48/64 | 1.86 cm | 48/64 |
| train-split | 3 | FL | 48/64 | 0.30 cm | 48/64 |
| train-split | 3 | FR | 48/64 | 0.94 cm | 48/64 |
| train-split | 3 | RL | 48/64 | 1.10 cm | 48/64 |
| train-split | 3 | RR | 48/64 | 0.89 cm | 48/64 |

## 공통 지표 분리

| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |
|---|---:|---:|---:|
| parent | 0 | 64/64 | 64/64 |
| train-continuous | 0 | 64/64 | 64/64 |
| train-split | 0 | 64/64 | 64/64 |
| parent | 1 | 64/64 | 64/64 |
| train-continuous | 1 | 48/64 | 48/64 |
| train-split | 1 | 49/64 | 64/64 |
| parent | 2 | 64/64 | 64/64 |
| train-continuous | 2 | 48/64 | 48/64 |
| train-split | 2 | 48/64 | 48/64 |
| parent | 3 | 64/64 | 64/64 |
| train-continuous | 3 | 48/64 | 48/64 |
| train-split | 3 | 48/64 | 48/64 |

## 출발 계약과 궤적 부분집합

3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.

| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |
|---|---:|---:|---:|---:|
| parent | 0 | 3 cm | 64/64 | 48/64 |
| train-continuous | 0 | 3 cm | 64/64 | 64/64 |
| train-split | 0 | 3 cm | 64/64 | 64/64 |
| parent | 1 | 3 cm | 64/64 | 48/64 |
| train-continuous | 1 | 3 cm | 48/64 | 48/64 |
| train-split | 1 | 3 cm | 64/64 | 49/64 |
| parent | 2 | 3 cm | 64/64 | 64/64 |
| train-continuous | 2 | 3 cm | 48/64 | 48/64 |
| train-split | 2 | 3 cm | 48/64 | 48/64 |
| parent | 3 | 3 cm | 64/64 | 48/64 |
| train-continuous | 3 | 3 cm | 48/64 | 48/64 |
| train-split | 3 | 3 cm | 48/64 | 48/64 |

## 거리별 평가

| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |
|---|---:|---:|---:|---:|---:|---:|---:|
| parent | 0 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 0 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 0 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 0 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-continuous | 0 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 0 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 0 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 0 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 0 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 0 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 0 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 0 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 1 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 1 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 1 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 1 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-continuous | 1 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| train-continuous | 1 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 1 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 1 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 1 | 0 cm | 1/16 | 16/16 | 16/16 | 16/16 | 1/16 |
| train-split | 1 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 1 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 1 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 2 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 2 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 2 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 2 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 2 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| train-continuous | 2 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 2 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 2 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 2 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| train-split | 2 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 2 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 2 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 3 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 3 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 3 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| parent | 3 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| train-continuous | 3 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| train-continuous | 3 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 3 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-continuous | 3 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 3 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| train-split | 3 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 3 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| train-split | 3 | 15 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |

![학습 곡선](figures/p2-29-regression-learning.png)

학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.

## 종료 단계

- GROUP parent seed 0: `{'2:2': 64}`
- GROUP train-continuous seed 0: `{'2:2': 64}`
- GROUP train-split seed 0: `{'2:2': 64}`
- GROUP parent seed 1: `{'2:2': 64}`
- GROUP train-continuous seed 1: `{'0:0': 16, '2:2': 48}`
- GROUP train-split seed 1: `{'2:2': 64}`
- GROUP parent seed 2: `{'2:2': 64}`
- GROUP train-continuous seed 2: `{'0:0': 16, '2:2': 48}`
- GROUP train-split seed 2: `{'0:0': 16, '2:2': 48}`
- GROUP parent seed 3: `{'2:2': 64}`
- GROUP train-continuous seed 3: `{'0:0': 16, '2:2': 48}`
- GROUP train-split seed 3: `{'0:0': 16, '2:2': 48}`

## 마지막 제어 표본의 안정화 조건 위반

복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.

- parent seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- train-continuous seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- train-split seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- parent seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- train-continuous seed 1: `{'height': 0, 'vertical_speed': 11, 'angular_speed': 8, 'foot_target': 4, 'contact_state': 15, 'support_history': 16}`
- train-split seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- parent seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- train-continuous seed 2: `{'height': 0, 'vertical_speed': 16, 'angular_speed': 16, 'foot_target': 0, 'contact_state': 16, 'support_history': 16}`
- train-split seed 2: `{'height': 0, 'vertical_speed': 16, 'angular_speed': 16, 'foot_target': 0, 'contact_state': 16, 'support_history': 16}`
- parent seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- train-continuous seed 3: `{'height': 0, 'vertical_speed': 16, 'angular_speed': 16, 'foot_target': 16, 'contact_state': 16, 'support_history': 16}`
- train-split seed 3: `{'height': 0, 'vertical_speed': 16, 'angular_speed': 16, 'foot_target': 16, 'contact_state': 16, 'support_history': 16}`

## 해석 및 다음 판단

분석 중. 표만으로 모델 승격을 결정하지 않는다.

## 범위·재현

개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종 병렬 평가 영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.

실행 목록 및 보고서 명세: `configs/reports/p2-29-regression.json`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다.
