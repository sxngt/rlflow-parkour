# T0 목표 발 디딤 계약 v1

2026-09-10. **정답 상태를 이용한 정적 목표 접촉 과제**다. 동적 보행·도약·Planner 결과가 아니다.

## 과제

A1의 네 발에 episode 동안 고정된 XY 목표를 준다. 초기 자산 발 위치 주위 각 축 ±0.06 m 균일 분포에서 표본을 만든다. 평지 기본이며, 선택적 넓은 지지 블록 높이를 설정할 수 있다. 후자는 불연속 stepping stones 코스가 아니다.

발 순서는 실제 자산 이름으로 조회해 센서 순서와 일치하는지 검사한다. 목표의 기준 XY는 실행 메타데이터 `nominal_foot_xy_m`에 기록한다. 시작 시 root pose·joint pose를 기본 자세로 reset한다. 시뮬레이션의 정답 선속도·자세·합력 사용을 명시한다.

## 관측과 행동

| 관측 index | 의미 |
|---|---|
| 0:3 | root 선속도, body frame, 정답 |
| 3:6 | 각속도, body frame |
| 6:9 | projected gravity |
| 9:21 | 기본 자세 대비 관절 위치 |
| 21:33 | 관절 속도 ×0.05 |
| 33:45 | 이전 실행 행동 |
| 45:57 | 발별 world target를 현재 body frame으로 변환한 xyz |
| 57:61 | 정답 발 합력 기반 접촉 hysteresis |

PPO policy/critic 모두 동일한 61차원 관측을 사용한다. 학습된 경험적 normalization을 checkpoint에 보관하고 평가 중 갱신하지 않는다. 센서 기반 추정기나 RQ2의 B0 정의는 아직 아니다.

행동은 12차원, [-1,1] clipping, 기본 관절 위치 + 0.35 rad × 행동. Isaac Lab 기본 DC motor limit 유지. Physics 200 Hz, action 50 Hz. 학습은 rsl-rl-lib 2.3.3 PPO이며 과거 궤적 replay를 섞지 않는다.

## 보상·종료

발 XY 오차의 지수형 점수와 접촉 시 점수, 몸체 자세·높이·목표 중심, 행동 변화·토크·각속도 비용을 합산한다. 시간 밀도 보상은 dt로 적분한다. 성공 +2, 실패 -2. 정확한 계수는 `src/parkour/task.py`가 정의하며 source hash를 run에 남긴다.

접촉 onset >5 N, release <2 N. 초기 0.5초 이후 네 발 모두 XY 오차 <0.035 m와 접촉을 0.2초 유지하면 성공. 몸체 접촉·높이 하락·60도 초과 기울기·0.6 m 이상 이탈은 실패다. 4초 제한은 실제 실패와 구분한 truncation이다. PPO timeout bootstrap을 사용한다.

현재의 성공 검사는 평지 XY 접촉 기준이다. 좁은 발판·경사면을 도입하기 전 표면 ID·접촉 위치·법선 및 z 일치 판정으로 강화해야 한다. 정적 자세 유지의 성능과 목표를 바꾼 정책의 성능을 따로 비교한다.

## 평가

- 개발 seed 10000부터, 각 시나리오별 독립 Python RNG로 발 목표를 생성한다.
- 환경 개수나 다른 난수 호출이 바뀌어도 앞선 시나리오 표본은 동일하다.
- 각 환경에서 첫 episode 하나씩 전부 수집한다. 먼저 완료한 일부만 집계하지 않는다.
- simulator 자동 reset 이전에 terminal KPI를 복사하고, 완료한 env의 후속 episode를 집계에서 제외한다.
- 정책·기본 자세·목표 관측 셔플 비교. 셔플은 동일 모델의 목표 의존성 진단이며 별도 학습 절제 실험이 아니다.
- 성공률 Wilson 95% 구간은 episode 표본 불확실성이다. 학습 seed 간 불확실성을 대신하지 않는다.
- 최종 시험군은 아직 사용하지 않았다. 현재 모든 결과는 파일럿이다.

## 저장·재개

Checkpoint는 policy, optimizer, adaptive learning rate, observation normalization, Python/NumPy/Torch/CUDA/scenario RNG, 고정 curriculum, 완료 iteration·총 step을 저장한다. 임시 저장→재로드 확인→파일 교체→SHA-256 완료 sidecar 순서다.

재개는 반드시 새 attempt 디렉터리이며 parent checkpoint hash를 남긴다. 물리 장면은 새 episode 경계에서 시작하므로 미완료 episode는 버리고 bitwise 재현을 주장하지 않는다. 저장된 policy·optimizer·normalization·난수 상태로 다음 PPO rollout을 새로 수집한다.

## GPU 실행

`run_job.py`는 UUID를 CUDA_VISIBLE_DEVICES로 지정하고 host graphics index를 별도로 매핑한다. 한 GPU에 한 자체 작업만 허용하는 파일 lease를 사용한다. subprocess에 시간 예산을 적용하고 관측한 worker PID의 GPU 사용·종료 후 해제를 기록한다. 이 wrapper는 아직 queue·aging·deadline·backfill이 있는 resource broker가 아니다.

Isaac Sim 4.5 종료 플러그인 정체를 우회하려고 전용 worker는 파일 저장·writer 종료 후 자체 프로세스를 종료한다. 정상 플러그인 teardown으로 표현하지 않는다. supervisor가 exit code와 실제 GPU PID 해제를 확인한다. supervisor의 crash reconciliation은 후속 과제다.
