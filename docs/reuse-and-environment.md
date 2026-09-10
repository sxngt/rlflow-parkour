# 재사용 및 환경 기록

## 이번 구현

`parkour`의 task/학습/평가/실행 wrapper 코드는 이 프로젝트에서 작성했다. 알고리즘은 설치된 rsl-rl PPO를 호출한다. 알고리즘 자체를 신규 연구 기여로 보지 않는다.

검토한 로컬 자료:

- `../master-thesis/docs/setup.md`: 서버 설치 위치와 버전, 공유 GPU 주의, 영상과 학습 분리 경험.
- `../master-thesis/src/quadruped_rl/envs/backends/isaaclab_backend.py`: AppLauncher 초기화 순서, A1 및 센서 매핑.
- `../master-thesis/scripts/record_video.py`: headless 렌더링과 shutdown 정체 경험.
- 설치된 Isaac Lab의 `direct/anymal_c` 예제, DirectRLEnv, RslRlVecEnvWrapper와 rsl-rl OnPolicyRunner/PPO: 실행 lifecycle와 adapter 계약 확인.

기존 thesis의 reward/algorithm/LLM coach 코드는 복사하지 않았다. 해당 프로젝트와 Isaac Lab 설치 파일을 수정하지 않았다. 외부 서비스 호출이나 유료 코칭을 사용하지 않는다.

## 실제 사용 환경

- Isaac Sim 4.5.0, Isaac Lab release v2.1.1 (`90b79bb2d44feb8d833f260f2bf37da3487180ba`).
- Python 3.10 번들 환경, `isaaclab` package 0.41.3 (동일 release의 extension version).
- Torch 2.7.0+cu128, NumPy 1.26.0, rsl-rl-lib 2.3.3.
- 전체 Python freeze는 로컬 `artifacts/environment-freeze.txt`에 보관.
- 이는 기존 서버의 **실행 확인 환경**이다. 새 container/다른 호스트 재설치 검증이나 완전한 dependency lock 완료를 뜻하지 않는다.
- NVIDIA 배포 A1 USD를 설치된 Isaac Lab 설정으로 읽는다. 자산 원본을 저장소에 복사하지 않는다. 모든 USD 의존 자산 hash 고정은 미완료다.

작업별 `run.json`의 config/source hash, checkpoint 및 산출물 hash와 supervisor exit/해제 증거를 함께 확인한다. 초기 실행의 source는 당시 hash와 일치하는 파일만 `source-snapshot/`에 보존했다.

## 자원 권한

사용자는 2026-09-10 이 서버의 RTX 4090 네 장 모두 본인 소유이며 연구에 사용할 수 있다고 명시했다. 네 장을 독립 seed 학습·평가에 사용한다. 장치별 메모리는 합쳐 쓰지 않는다. 라이브러리·정책·환경을 바꾸는 실험은 별도 설정/attempt로 남긴다.
