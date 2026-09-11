# P2-13 · 대규모 환경 minibatch 비교

8192환경200update에서 minibatch수를4→32로 변경한다. 총환경step과gradient갱신수를 P2-11에맞추지만정책수집빈도는같지않다.

비교 전체 157,286,400 환경 step, 신규 157,286,400step. [사전 프로토콜](p2-13-protocol.md).

| 발 | 조건 | seed | 수평 도약 성공 | 필요 착지 완료 | 낙상 | 시간초과 | ≥20ms 전 발 무접촉 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| GROUP | minibatches-32 | 0 | 0/64 | 0/64 | 0/64 | 64/64 | 0/64 |
| GROUP | minibatches-32 | 1 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |
| GROUP | minibatches-32 | 2 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |
| GROUP | minibatches-32 | 3 | 0/64 | 0/64 | 0/64 | 64/64 | 64/64 |

## 도약 계약 지표

| 조건 | seed | 유효 비행 | 비행 후 재접촉 | 수평 도약 성공 | 비발 접촉 종료 | 평균 비행 apex 상승 | 높이 명령 충족 | 네 발 첫 접촉 반경 내 | 최종 높이 범위 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| minibatches-32 | 0 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 0/64 |
| minibatches-32 | 1 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 0/64 |
| minibatches-32 | 2 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 0/64 |
| minibatches-32 | 3 | 0/64 | 0/64 | 0/64 | 0 | 0.00 cm | 0/64 | 0/64 | 0/64 |

## 발별 첫 접촉

오차 평균은 관측된 첫 접촉만 포함한다. 반경 내 수의 분모는 전체 episode이며 미접촉을 성공으로 세지 않는다.

| 조건 | seed | 발 | 관측 수 | 평균 오차 | 반경 내 |
|---|---:|---|---:|---:|---:|
| minibatches-32 | 0 | FL | 0/64 | N/A | 0/64 |
| minibatches-32 | 0 | FR | 0/64 | N/A | 0/64 |
| minibatches-32 | 0 | RL | 0/64 | N/A | 0/64 |
| minibatches-32 | 0 | RR | 0/64 | N/A | 0/64 |
| minibatches-32 | 1 | FL | 0/64 | N/A | 0/64 |
| minibatches-32 | 1 | FR | 0/64 | N/A | 0/64 |
| minibatches-32 | 1 | RL | 0/64 | N/A | 0/64 |
| minibatches-32 | 1 | RR | 0/64 | N/A | 0/64 |
| minibatches-32 | 2 | FL | 0/64 | N/A | 0/64 |
| minibatches-32 | 2 | FR | 0/64 | N/A | 0/64 |
| minibatches-32 | 2 | RL | 0/64 | N/A | 0/64 |
| minibatches-32 | 2 | RR | 0/64 | N/A | 0/64 |
| minibatches-32 | 3 | FL | 0/64 | N/A | 0/64 |
| minibatches-32 | 3 | FR | 0/64 | N/A | 0/64 |
| minibatches-32 | 3 | RL | 0/64 | N/A | 0/64 |
| minibatches-32 | 3 | RR | 0/64 | N/A | 0/64 |

## 공통 지표 분리

| 조건 | seed | 기존 안정화 달성 | 첫 접촉 네 발 반경 내 |
|---|---:|---:|---:|
| minibatches-32 | 0 | 0/64 | 0/64 |
| minibatches-32 | 1 | 0/64 | 0/64 |
| minibatches-32 | 2 | 0/64 | 0/64 |
| minibatches-32 | 3 | 0/64 | 0/64 |

## 출발 계약과 궤적 부분집합

3cm 내 성공 궤적 수는 현재 실행에서의 부분집합이다. 다른 출발 반경으로 재실행한 평가를 대체하지 않는다.

| 조건 | seed | 실행 출발 반경 | 3cm 내 출발 / 전체 | 3cm 내 성공 / 전체 |
|---|---:|---:|---:|---:|
| minibatches-32 | 0 | 3 cm | 0/64 | 0/64 |
| minibatches-32 | 1 | 3 cm | 0/64 | 0/64 |
| minibatches-32 | 2 | 3 cm | 0/64 | 0/64 |
| minibatches-32 | 3 | 3 cm | 0/64 | 0/64 |

## 거리별 평가

| 조건 | seed | 전방 목표 | 성공 | 출발 영역 | 실비행 이동 충족 | 첫 접촉 반경 | 안정화 |
|---|---:|---:|---:|---:|---:|---:|---:|
| minibatches-32 | 0 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 0 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 0 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 0 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 1 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 1 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 1 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 1 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 2 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 2 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 2 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 2 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 3 | 0 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 3 | 5 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 3 | 10 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |
| minibatches-32 | 3 | 15 cm | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |

![학습 곡선](figures/p2-13-learning.png)

학습 곡선은 각 update의 종료 episode 통계다. 고정 평가 결과와 구분한다. 종료 단계는 마지막 유효 200Hz 표본이며 실제 완료 여부는 terminal metrics를 우선한다.

## 종료 단계

- GROUP minibatches-32 seed 0: `{'0:0': 64}`
- GROUP minibatches-32 seed 1: `{'0:0': 64}`
- GROUP minibatches-32 seed 2: `{'0:0': 64}`
- GROUP minibatches-32 seed 3: `{'0:0': 64}`

## 마지막 제어 표본의 안정화 조건 위반

복수 위반을 허용한다. 연속 hold 전체 구간의 실패 원인과 같지 않으며, 기록되지 않은 과거 실행은 표시하지 않는다.

- minibatches-32 seed 0: `{'height': 0, 'vertical_speed': 0, 'angular_speed': 0, 'foot_target': 49, 'contact_state': 0, 'support_history': 0}`
- minibatches-32 seed 1: `{'height': 0, 'vertical_speed': 64, 'angular_speed': 0, 'foot_target': 64, 'contact_state': 64, 'support_history': 64}`
- minibatches-32 seed 2: `{'height': 0, 'vertical_speed': 27, 'angular_speed': 18, 'foot_target': 64, 'contact_state': 56, 'support_history': 64}`
- minibatches-32 seed 3: `{'height': 0, 'vertical_speed': 64, 'angular_speed': 4, 'foot_target': 64, 'contact_state': 64, 'support_history': 64}`

## 해석 및 다음 판단

네seed 모두성공0/64이다. minibatch표본수와총gradient갱신횟수를P2-11에맞춰도성능회복이확인되지않았다.
P2-12와같은환경step에서num_mini_batches4→32만변경한결과이며새정책데이터수집횟수는200으로같다. 실패원인을단일요인으로확정하지않는다.
학습4+평가4artifact감사와원본진단대조를통과했다. result영상4개보존. 8192규모를현재제어연구의기본값으로채택하지않고기존유효정책을다음지형검증에사용한다.

## 범위·재현

개발 조건의 탐색적 실험이다. 평가 episode 수와 독립 학습 seed 수를 구분하며 최종 시험 결과로 주장하지 않는다. 같은 발의 평가 시나리오가 동일함을 확인했다. 설정·checkpoint·원본200Hz NPZ는 artifacts, 최종16대병렬영상은 result에 보존한다. 재사용 대조군 원본은 변경하지 않는다.

실행 목록 및 보고서 명세: `configs/reports/p2-13.json`. 이 보고서는 `scripts/experiment_report.py`로 재생성한다.
