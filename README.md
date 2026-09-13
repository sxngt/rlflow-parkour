# parkour — RLflow 프로젝트

사전 지도 기반 Planner–RL Tracker 사족(Unitree A1) 파쿠르 연구. 2026-09-13 부터 새 실행은 RLflow(https://rlflow.kr/p/parkour) 로 제출하고,
`workspace/parkour` 에서 만들었던 실행 1,400여 개(학습 395·평가 903·probe 72, 영상 891)는 MLflow 실험 `parkour` 로 편입했다
(출처 태그 `legacy_path`, 콘솔 런 목록의 `legacy` 표시). 원본 워크스페이스는 그대로 두었다. 편입 절차·매핑은 플랫폼 문서
[프로젝트 › parkour](https://docs.rlflow.kr/projects/parkour/) 에 있다.

## RLflow 에서 실행

| 항목 | 값 |
|---|---|
| config | `configs/<name>.yaml` = 기존 `configs/<name>.json` 의 1:1 사본 (`scripts/sync_rlflow_configs.py`). 기본 `config.yaml` → `p3-70-control` |
| overrides | Hydra 점 경로. 예: `iterations=400 num_envs=512 runner.algorithm.learning_rate=5e-4 seed=3` |
| 체크포인트에서 시작 | `+fork_from=mlflow://<run_id>/checkpoints/step_<n>.pt` (새 계보) 또는 `+resume=…` (같은 계보 이어서) |
| 태그 | 제출 폼의 지형·과제·난이도·목적 축 (rlflow.yaml) + 자유 태그 `phase:P3` … → MLflow 태그 `rt.<key>` |
| 촬영 | 프로젝트 설정 → 촬영. 학습은 `--video`(parallel-training.mp4), 평가는 시나리오별 `evaluation.mp4` |

파이프라인: `train.py`(→ `scripts/train.py`) → candidate → `evaluate.py`(→ `scripts/evaluate.py`, `eval_suite/default.yaml`) → 게이트 → `export.py`(ONNX) → validated.
세 진입점은 연구 코드를 감싸는 얇은 래퍼다. 지표 이름 매핑과 한계(env/ep_return 자리 채움 등)는 `train.py` 머리말 참고.

기존 모니터링 웹(`monitor/`, `web/`)은 RLflow 콘솔(런·정책·영상 라이브러리·Grafana)이 대신하므로 트리에서 제거했다 (git 이력에는 남아 있다).

---

# parkour

사전 지도 기반 Planner–RL Tracker 사족 파쿠르 연구 플랫폼. **현재 P3의 수평 발판 8회 연속 도약과 작은 간격 변화를 검증하고, P4 마찰 변화 학습을 진행 중**이다. 고정 mapped 정책 seed 2는 1.20m 발 목표 코스에서 64/64회 완주했지만, 후반 발판의 마찰 재질을 바꾸면 0/64회로 떨어졌다. 동일 예산의 저마찰 학습·기존 마찰 대조군을 비교한다.

이 결과는 `mapped_contact_v1`과 명시적 지도 경계를 사용하는 개발군 평가다. 기존 몸체 비행거리 기준과 구분하며, 고속·경사·급선회·실기 파쿠르 달성을 의미하지 않는다. [현재 실행과 검증 범위](docs/p4-02-progress.md), [긴 코스 결과](docs/p3-11-findings.md), [마찰 변화 결과](docs/p4-01-findings.md)를 확인할 수 있다.

연구를 이어갈 때는 [현재 연구 인계](docs/active-research.md)에서 시작한다.
- [단일 도약 학습 프로토콜](docs/p2-01-protocol.md)
- [공유 Tracker 결과](docs/step02e-results.md)
- [추가 학습·회귀 결과](docs/step02d-results.md)
- [정렬 비용 적용 시점 결과](docs/step02c-results.md)
- [최종 정렬 보상 비교 결과](docs/step02b-results.md)
- [발별 단독 이동 결과](docs/step02a-results.md)
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

P2-09 거리 확장: [결과](docs/p2-09-results.md), [3cm 재평가](docs/p2-09-strict-results.md). 다음 [P2-10](docs/p2-10-protocol.md)은 같은 조건에서3cm 출발을 직접 학습한다.
