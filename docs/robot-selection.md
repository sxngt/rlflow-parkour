# 첫 기준 로봇: Unitree A1

결정일: 2026-09-10. 상태: P0 모델 선정. 프로젝트 이름은 `parkour`.

## 판단

현재 접근 가능한 자산과 실제 파쿠르 연구 근거를 함께 고려하면 A1이 첫 기준선에 가장 적합하다.
모든 후보보다 물리적으로 우수하다는 결론이나, 이 프로젝트의 파쿠르 성공 보장은 아니다.

| 후보 | 근거 및 제약 | 결정 |
|---|---|---|
| Raibo | 핵심 참고 논문의 실제 로봇. 확인한 프로젝트 페이지에서 즉시 사용 가능한 공식 Isaac Lab 모델·구동기 패키지를 확보하지 못함 | 설계 참고; 자산 확보 시 재검토 |
| Unitree A1 | Extreme Parkour가 사용한 하드웨어. 공개 구현의 실제 URDF도 A1. 설치된 Isaac Lab 및 기존 master-thesis 지원 | 첫 기준 모델 |
| Unitree Go1 | 설치된 Isaac Lab 자산 존재; 기본 구동기는 별도 학습된 actuator network에 의존 | 후속 후보 |
| Unitree Go2 | 설치된 Isaac Lab 자산 및 DC motor 설정 존재. 최신 기종이라는 이유만으로 이 연구에서 우위라고 판단할 근거 없음 | 후속 후보 |
| ANYmal | ANYmal Parkour 연구 실적과 Isaac Lab 자산 존재. 로봇 세대·구동기 모델·논문과의 일치를 따로 확인해야 함 | 후속 비교 후보 |

주의: Extreme Parkour의 `go1_config.py`라는 파일명만 보고 Go1을 사용했다고 판단하면 안 된다.
확인한 코드의 `asset.file`은 `resources/robots/a1/urdf/a1.urdf`이며 원문도 A1을 명시한다.

## 초기 시뮬레이션 계약

- Isaac Lab 2.1.1의 `UNITREE_A1_CFG`를 사용한다. 외형만 A1인 다른 모델로 바꾸지 않는다.
- 12개 관절, 발 4개. 관절 순서와 발 순서는 실행 시 이름으로 기록한다.
- 초기 구동기는 기본 DC motor 모델: effort/saturation 33.5 Nm, velocity 21 rad/s, stiffness 25, damping 0.5.
- 이 값은 설치된 시뮬레이터 설정이며 실기 시스템 식별 결과가 아니다.
- 첫 smoke는 200 Hz physics, 기본 관절 자세 유지, 평지, 정답 접촉 합력 기록이다.
- 기본 설정의 self-collision 비활성화는 이후 동적 실행 전에 검토할 항목이다.
- 높은 점프를 만들기 위해 토크·속도 한계를 임의로 키우지 않는다.
- 후속 Tracker는 목표 발 디딤 조건부 PPO로 작성한다. 기존 보행 정책은 직접 호환된다고 가정하지 않는다.

## 출처와 재사용

1. [Raibo 논문](https://arxiv.org/html/2506.02835v1): Planner–Tracker 구조와 Raibo 실험 근거.
2. [Raibo 프로젝트](https://awesomericky.github.io/projects/Quadruped_parkour/index.html): 확인한 공개 진입점. 공식 코드가 존재하지 않는다고 단정하지 않는다.
3. [Extreme Parkour 원문](https://arxiv.org/html/2309.14341v1): A1 파쿠르 하드웨어 근거.
4. [공개 모델 설정](https://github.com/chengxuxin/extreme-parkour/blob/main/legged_gym/legged_gym/envs/go1/go1_config.py): 실제 A1 URDF 사용 확인.
5. [Isaac Lab 고정 버전 모델 설정](https://github.com/isaac-sim/IsaacLab/blob/v2.1.1/source/isaaclab_assets/isaaclab_assets/robots/unitree.py).
6. [ANYmal Parkour](https://arxiv.org/abs/2306.14874).
7. 로컬 `../master-thesis/src/quadruped_rl/envs/backends/isaaclab_backend.py`, `docs/setup.md`, `scripts/record_video.py`: AppLauncher 선행 초기화, A1 매핑, 서버 설치 경로, 기록·평가 주의점 참고. 알고리즘·보상 코드는 복사하지 않음.

Isaac Lab 코드의 BSD-3-Clause와 다운로드되는 USD·메시·구동기 파일의 사용 조건은 별개다.
[Unitree ROS 저장소 라이선스](https://github.com/unitreerobotics/unitree_ros/blob/master/LICENSE)를 NVIDIA 배포 USD의 라이선스로 대체하지 않는다.
설치된 Isaac Lab의 `docs/licenses/assets/unitree-license.txt`에서도 Unitree BSD-3-Clause 고지를 확인했다.
현재 저장소에는 제3자 자산을 재배포하지 않는다. 공개 배포 전 자산별 조건과 hash를 확정한다.
