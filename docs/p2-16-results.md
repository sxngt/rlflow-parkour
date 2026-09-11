# P2-16 · 목표 거리 커리큘럼

동일 발판과 예산에서 거리 커리큘럼 4seed를 기존 P2-15 고정 분포와 비교한다. 기존 대조 결과 재사용이며 동시 무작위 실험은 아니다.

고유 학습 run 기준 314,572,800 환경 step, 신규 157,286,400step. [사전 프로토콜](p2-16-protocol.md).

| 발 | 조건 | seed | 목표 도약 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GROUP | fixed-distance | 0 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |
| GROUP | fixed-distance | 1 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |
| GROUP | fixed-distance | 2 | 0/64 | 64/64 | 0/64 | 64/64 | 64/64 |
| GROUP | fixed-distance | 3 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | distance-curriculum | 0 | 32/64 | 64/64 | 0/64 | 32/64 | 64/64 |
| GROUP | distance-curriculum | 1 | 1/64 | 64/64 | 0/64 | 63/64 | 64/64 |
| GROUP | distance-curriculum | 2 | 48/64 | 64/64 | 0/64 | 16/64 | 64/64 |
| GROUP | distance-curriculum | 3 | 5/64 | 64/64 | 0/64 | 59/64 | 64/64 |

## 도약 계약 지표

| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 목표 도약 성공 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed-distance | 0 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 18/64 |
| fixed-distance | 1 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 64/64 |
| fixed-distance | 2 | 64/64 | 64/64 | 0/64 | 0 | 11.13 cm | 64/64 | 11/64 | 0/64 |
| fixed-distance | 3 | 64/64 | 64/64 | 48/64 | 0 | 12.86 cm | 64/64 | 64/64 | 0/64 |
| distance-curriculum | 0 | 64/64 | 64/64 | 32/64 | 0 | 9.10 cm | 64/64 | 64/64 | 0/64 |
| distance-curriculum | 1 | 64/64 | 64/64 | 1/64 | 0 | 7.60 cm | 64/64 | 47/64 | 0/64 |
| distance-curriculum | 2 | 64/64 | 64/64 | 48/64 | 0 | 8.58 cm | 64/64 | 64/64 | 0/64 |
| distance-curriculum | 3 | 64/64 | 64/64 | 5/64 | 0 | 7.02 cm | 53/64 | 16/64 | 0/64 |

## 발별 첫 접촉

오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.

| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |
|---|---:|---|---:|---:|---:|
| fixed-distance | 0 | FL | 0/64 | N/A | 0/64 |
| fixed-distance | 0 | FR | 0/64 | N/A | 0/64 |
| fixed-distance | 0 | RL | 0/64 | N/A | 0/64 |
| fixed-distance | 0 | RR | 0/64 | N/A | 0/64 |
| fixed-distance | 1 | FL | 0/64 | N/A | 0/64 |
| fixed-distance | 1 | FR | 0/64 | N/A | 0/64 |
| fixed-distance | 1 | RL | 0/64 | N/A | 0/64 |
| fixed-distance | 1 | RR | 0/64 | N/A | 0/64 |
| fixed-distance | 2 | FL | 64/64 | 6.71 cm | 28/64 |
| fixed-distance | 2 | FR | 64/64 | 3.25 cm | 50/64 |
| fixed-distance | 2 | RL | 64/64 | 3.66 cm | 45/64 |
| fixed-distance | 2 | RR | 64/64 | 7.41 cm | 13/64 |
| fixed-distance | 3 | FL | 64/64 | 2.55 cm | 64/64 |
| fixed-distance | 3 | FR | 64/64 | 2.02 cm | 64/64 |
| fixed-distance | 3 | RL | 64/64 | 2.39 cm | 64/64 |
| fixed-distance | 3 | RR | 64/64 | 1.88 cm | 64/64 |
| distance-curriculum | 0 | FL | 64/64 | 3.59 cm | 64/64 |
| distance-curriculum | 0 | FR | 64/64 | 1.15 cm | 64/64 |
| distance-curriculum | 0 | RL | 64/64 | 1.50 cm | 64/64 |
| distance-curriculum | 0 | RR | 64/64 | 3.15 cm | 64/64 |
| distance-curriculum | 1 | FL | 64/64 | 3.24 cm | 48/64 |
| distance-curriculum | 1 | FR | 64/64 | 2.42 cm | 64/64 |
| distance-curriculum | 1 | RL | 64/64 | 2.49 cm | 63/64 |
| distance-curriculum | 1 | RR | 64/64 | 2.84 cm | 64/64 |
| distance-curriculum | 2 | FL | 64/64 | 2.05 cm | 64/64 |
| distance-curriculum | 2 | FR | 64/64 | 1.37 cm | 64/64 |
| distance-curriculum | 2 | RL | 64/64 | 1.81 cm | 64/64 |
| distance-curriculum | 2 | RR | 64/64 | 2.11 cm | 64/64 |
| distance-curriculum | 3 | FL | 64/64 | 1.16 cm | 64/64 |
| distance-curriculum | 3 | FR | 64/64 | 1.48 cm | 64/64 |
| distance-curriculum | 3 | RL | 64/64 | 1.01 cm | 64/64 |
| distance-curriculum | 3 | RR | 64/64 | 6.86 cm | 16/64 |

## 공통 지표 분리

| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |
|---|---:|---:|---:|
| fixed-distance | 0 | 0/64 | 0/64 |
| fixed-distance | 1 | 0/64 | 0/64 |
| fixed-distance | 2 | 0/64 | 11/64 |
| fixed-distance | 3 | 64/64 | 64/64 |
| distance-curriculum | 0 | 64/64 | 64/64 |
| distance-curriculum | 1 | 4/64 | 47/64 |
| distance-curriculum | 2 | 64/64 | 64/64 |
| distance-curriculum | 3 | 38/64 | 16/64 |

## 출발 계약과 궤적 부분집합

3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.

| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |
|---|---:|---:|---:|---:|
| fixed-distance | 0 | 3 cm | 0/64 | 0/64 |
| fixed-distance | 1 | 3 cm | 0/64 | 0/64 |
| fixed-distance | 2 | 3 cm | 64/64 | 0/64 |
| fixed-distance | 3 | 3 cm | 64/64 | 48/64 |
| distance-curriculum | 0 | 3 cm | 64/64 | 32/64 |
| distance-curriculum | 1 | 3 cm | 64/64 | 1/64 |
| distance-curriculum | 2 | 3 cm | 64/64 | 48/64 |
| distance-curriculum | 3 | 3 cm | 64/64 | 5/64 |

## 거리별 평가

| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed-distance | 0 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 0 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 0 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 0 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 1 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 1 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 1 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 1 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| fixed-distance | 2 | 0 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| fixed-distance | 2 | 5 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| fixed-distance | 2 | 10 cm | 0/16 | 16/16 | 13/16 | 2/16 | 0/16 |
| fixed-distance | 2 | 15 cm | 0/16 | 16/16 | 0/16 | 9/16 | 0/16 |
| fixed-distance | 3 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| fixed-distance | 3 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| fixed-distance | 3 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| fixed-distance | 3 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| distance-curriculum | 0 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| distance-curriculum | 0 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| distance-curriculum | 0 | 10 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| distance-curriculum | 0 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| distance-curriculum | 1 | 0 cm | 0/16 | 16/16 | 16/16 | 0/16 | 0/16 |
| distance-curriculum | 1 | 5 cm | 1/16 | 16/16 | 16/16 | 16/16 | 1/16 |
| distance-curriculum | 1 | 10 cm | 0/16 | 16/16 | 16/16 | 16/16 | 0/16 |
| distance-curriculum | 1 | 15 cm | 0/16 | 16/16 | 0/16 | 15/16 | 3/16 |
| distance-curriculum | 2 | 0 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| distance-curriculum | 2 | 5 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| distance-curriculum | 2 | 10 cm | 16/16 | 16/16 | 16/16 | 16/16 | 16/16 |
| distance-curriculum | 2 | 15 cm | 0/16 | 16/16 | 0/16 | 16/16 | 16/16 |
| distance-curriculum | 3 | 0 cm | 5/16 | 16/16 | 16/16 | 16/16 | 5/16 |
| distance-curriculum | 3 | 5 cm | 0/16 | 16/16 | 16/16 | 0/16 | 16/16 |
| distance-curriculum | 3 | 10 cm | 0/16 | 16/16 | 15/16 | 0/16 | 16/16 |
| distance-curriculum | 3 | 15 cm | 0/16 | 16/16 | 0/16 | 0/16 | 1/16 |

![학습 곡선](figures/p2-16-learning.png)

학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.

## 종료 단계

- GROUP fixed-distance seed 0: `{'0:0': 64}`
- GROUP fixed-distance seed 1: `{'0:0': 64}`
- GROUP fixed-distance seed 2: `{'2:2': 64}`
- GROUP fixed-distance seed 3: `{'2:2': 64}`
- GROUP distance-curriculum seed 0: `{'2:2': 64}`
- GROUP distance-curriculum seed 1: `{'2:2': 64}`
- GROUP distance-curriculum seed 2: `{'2:2': 64}`
- GROUP distance-curriculum seed 3: `{'2:2': 64}`

## 마지막 제어 표본의 안정화 조건 위반

복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.

- fixed-distance seed 0: `{'height': 18, 'vertical_speed': 64, 'angular_speed': 0, 'foot_target': 64, 'contact_state': 64, 'support_history': 64}`
- fixed-distance seed 1: `{'height': 64, 'vertical_speed': 61, 'angular_speed': 51, 'foot_target': 64, 'contact_state': 8, 'support_history': 13}`
- fixed-distance seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 2, 'foot_target': 60, 'contact_state': 32, 'support_history': 53}`
- fixed-distance seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- distance-curriculum seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- distance-curriculum seed 1: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 2, 'foot_target': 56, 'contact_state': 11, 'support_history': 31}`
- distance-curriculum seed 2: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 0, 'contact_state': 0, 'support_history': 0}`
- distance-curriculum seed 3: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 10, 'contact_state': 0, 'support_history': 0}`

## 해석 및 다음 판단

분석 중. 표만으로 모델 승격을 결정하지 않는다.

## 범위·재현

개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종 병렬 평가 영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.

실행 목록 및 보고서 명세: `configs/reports/p2-16.json`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다.
