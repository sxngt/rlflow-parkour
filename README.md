# parkour

사전 지도 기반 Planner–RL Tracker 사족 파쿠르 연구 플랫폼. 현재는 **A1의 보정된 자세에서 네 발을 순서대로 들어 목표에 놓는 T0S v2 PPO 파일럿** 단계다. 점프나 연속 파쿠르 성공을 의미하지 않는다.

- [실행별 최종 평가 영상 목록](result/README.md)
- [순차 발 디딤 과제 v2](docs/t0-sequential-v2.md)
- [영상 보관·자동 평가 규칙](docs/result-archive.md)
- [로봇 선정: Unitree A1](docs/robot-selection.md)
- [T0 관측·행동·보상·평가·재개 계약](docs/t0-contract.md)
- [환경·재사용·GPU 권한](docs/reuse-and-environment.md)
- [4 GPU 파일럿 결과와 검증 범위](docs/t0-pilot-results.md)
- [P0 진행 기록](docs/p0-status.md)

## 기존 서버에서 실행

Isaac Sim 4.5.0 / Isaac Lab 2.1.1 설치 환경을 사용한다. 기존 환경의 재설치는 필요 없다. 실행은 프로젝트 루트에서 한다.

```bash
# GPU 0의 로봇 1024개로 학습 후 최종 평가·MP4·result/ 정리까지 실행한다.
python3 scripts/run_job.py --gpu 0 --timeout 1200 train \
  --config configs/t0-sequential-ppo.json --out artifacts/my-train --iterations 800

# checkpoint에서 새 attempt로 재개한다. iterations는 추가 학습량이다.
python3 scripts/run_job.py --gpu 0 --timeout 600 train \
  --config configs/t0-sequential-ppo.json --out artifacts/my-resume --iterations 100 \
  --resume artifacts/my-train/checkpoint-000800.pt

# 고정 개발군의 모든 첫 episode를 평가하고 첫 episode MP4를 기록한다.
python3 scripts/run_job.py --gpu 1 evaluate \
  --config configs/t0-sequential-ppo.json \
  --out artifacts/my-eval --checkpoint artifacts/my-train/checkpoint-000800.pt --video

# 같은 과제의 기본 자세 대조군
python3 scripts/run_job.py --gpu 1 evaluate \
  --config configs/t0-sequential-ppo.json --out artifacts/my-zero --baseline zero --video

# 메타데이터·checkpoint hash·평가 완전성·GPU 해제 검사
python3 scripts/audit_artifacts.py artifacts/my-train artifacts/my-resume artifacts/my-eval
/mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh -m unittest discover -s tests -v
```

`--gpu`에 전체 GPU UUID를 직접 전달할 수도 있다. 출력 폴더는 항상 새 이름이어야 한다. 학습 seed 및 환경 수를 바꿀 때는 `--seed`, `--num-envs`를 사용한다. 기존 checkpoint의 seed/환경 수 변경은 단순 resume로 허용하지 않는다.

주요 출력:

- `run.json`, `config.json`: 실행·설정·코드 hash·계보.
- `metrics.jsonl`, `checkpoint-*.pt` + `.json`: 학습 진행과 무결성 확인된 모델 묶음.
- `evaluation.json`, `scenarios.json`: 고정 개발군 episode별 성능·종료 이유.
- `evaluation.mp4`, `replay.json`: 원본 프레임 영상과 simulator 시간·계획 목표·실제 발 위치·접촉 진행 단계.
- 실행 폴더 옆 `.log`, `.gpu.jsonl`, `.supervisor.json`: 로그·GPU PID 관측·종료 및 자원 회수.

## 최소 모델 smoke

기존 `scripts/smoke_a1.py`는 모델·접촉·영상 검사용으로 유지한다. 일반 학습은 위 supervisor를 사용한다. 초기 smoke의 Isaac Sim 종료에는 시간 제한 강제 종료가 필요했다. 현재 전용 worker는 모든 파일을 저장한 후 자체 프로세스를 종료하고 supervisor가 GPU 해제를 확인한다.

현재는 정답 상태를 쓰는 평지의 순차 lift→place 과제다. 동적 Tracker, 불연속 지형 Planner, 센서 적응 비교, 실패 커리큘럼, 웹 서비스 및 장기 scheduler는 후속 작업이다.

순차 과제 4-seed 결과와 병렬 촬영 기록: [T0S-v2 결과](docs/t0-sequential-results.md).

## 연구 모니터링 웹

[공인 주소에서 열기](http://203.241.249.48:18710) · [서버에서 열기](http://127.0.0.1:18710) · [Tailscale에서 열기](http://100.104.103.77:18710)

GPU 현황, 학습·평가 지표, 실행 비교, 실제 학습/평가 영상, 시간 연동 위치 기록, 연구 파일 탐색을 제공합니다. 새 결과는 자동으로 편입됩니다. [설치·운영·검증 기록](docs/monitoring-web.md).

최근 연구: [P1 · hopping 진단 결과](docs/hopping-diagnosis-results.md) · [연구 phase·태그 사용법](docs/research-phases.md).

최근 비교: [Step 02 · 3발 지지와 안정화 파일럿](docs/step02-results.md) — 수직 속도 벌점 A/B, 두 seed씩 평가. 아직 완주 정책을 확보하지 못했습니다.
