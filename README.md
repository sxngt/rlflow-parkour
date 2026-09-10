# parkour

사전 지도 기반 Planner–RL Tracker 사족 파쿠르 연구 플랫폼. 현재는 **A1 모델 검증과 T0 목표 발 디딤 PPO 파일럿** 단계다. 점프나 연속 파쿠르 성공을 의미하지 않는다.

- [로봇 선정: Unitree A1](docs/robot-selection.md)
- [T0 관측·행동·보상·평가·재개 계약](docs/t0-contract.md)
- [환경·재사용·GPU 권한](docs/reuse-and-environment.md)
- [4 GPU 파일럿 결과와 검증 범위](docs/t0-pilot-results.md)
- [P0 진행 기록](docs/p0-status.md)

## 기존 서버에서 실행

Isaac Sim 4.5.0 / Isaac Lab 2.1.1 설치 환경을 사용한다. 기존 환경의 재설치는 필요 없다. 실행은 프로젝트 루트에서 한다.

```bash
# GPU 0을 UUID로 해석하여 단일 GPU 작업을 실행한다.
python3 scripts/run_job.py --gpu 0 --timeout 600 train \
  --out artifacts/my-train --iterations 100

# checkpoint에서 새 attempt로 재개한다. iterations는 추가 학습량이다.
python3 scripts/run_job.py --gpu 0 --timeout 600 train \
  --out artifacts/my-resume --iterations 100 \
  --resume artifacts/my-train/checkpoint-000100.pt

# 고정 개발군의 모든 첫 episode를 평가하고 첫 episode MP4를 기록한다.
python3 scripts/run_job.py --gpu 1 evaluate \
  --out artifacts/my-eval --checkpoint artifacts/my-train/checkpoint-000100.pt --video

# 같은 과제의 기본 자세 대조군
python3 scripts/run_job.py --gpu 1 evaluate \
  --out artifacts/my-zero --baseline zero

# 메타데이터·checkpoint hash·평가 완전성·GPU 해제 검사
python3 scripts/audit_artifacts.py artifacts/my-train artifacts/my-resume artifacts/my-eval
python3 -m unittest discover -s tests -v
```

`--gpu`에 전체 GPU UUID를 직접 전달할 수도 있다. 출력 폴더는 항상 새 이름이어야 한다. 학습 seed 및 환경 수를 바꿀 때는 `--seed`, `--num-envs`를 사용한다. 기존 checkpoint의 seed/환경 수 변경은 단순 resume로 허용하지 않는다.

주요 출력:

- `run.json`, `config.json`: 실행·설정·코드 hash·계보.
- `metrics.jsonl`, `checkpoint-*.pt` + `.json`: 학습 진행과 무결성 확인된 모델 묶음.
- `evaluation.json`, `scenarios.json`: 고정 개발군 episode별 성능·종료 이유.
- `evaluation.mp4`, `replay.json`: 원본 프레임 영상과 simulator 시간·행동·계획 목표·실제 발 위치.
- 실행 폴더 옆 `.log`, `.gpu.jsonl`, `.supervisor.json`: 로그·GPU PID 관측·종료 및 자원 회수.

## 최소 모델 smoke

기존 `scripts/smoke_a1.py`는 모델·접촉·영상 검사용으로 유지한다. 일반 학습은 위 supervisor를 사용한다. 초기 smoke의 Isaac Sim 종료에는 시간 제한 강제 종료가 필요했다. 현재 전용 worker는 모든 파일을 저장한 후 자체 프로세스를 종료하고 supervisor가 GPU 해제를 확인한다.

현재는 정답 상태의 정적 목표 접촉 과제다. 동적 Tracker, 불연속 지형 Planner, 센서 적응 비교, 실패 커리큘럼, 웹 서비스 및 장기 scheduler는 후속 작업이다.
