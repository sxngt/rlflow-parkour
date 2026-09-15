# RLflow 에서 parkour 실행하기

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
| fork LR | `+fork_lr=inherit` — 부모 체크포인트의 마지막 adaptive LR(~1.5e-5, 하한 1e-5)로 시작. config LR(2e-4)로 재시작하면 첫 PPO 업데이트가 성숙 정책을 무너뜨린다(c21/c28/c36/c41 붕괴 원인). 숫자면 부모 LR 의 배수. MLflow 파라미터 `fork_learning_rate` |
| 태그 | 제출 폼의 지형·과제·난이도·목적 축 (rlflow.yaml) + 자유 태그 `phase:P3` … → MLflow 태그 `rt.<key>` |
| 촬영 | 프로젝트 설정 → 촬영. 학습은 `--video`(parallel-training.mp4), 평가는 시나리오별 `evaluation.mp4` |

파이프라인: `train.py`(→ `scripts/train.py`) → candidate → `evaluate.py`(→ `scripts/evaluate.py`, `eval_suite/default.yaml`) → 게이트 → `export.py`(ONNX) → validated.
세 진입점은 연구 코드를 감싸는 얇은 래퍼다. 지표 이름 매핑과 한계(env/ep_return 자리 채움 등)는 `train.py` 머리말 참고.

기존 모니터링 웹(`monitor/`, `web/`)은 RLflow 콘솔(런·정책·영상 라이브러리·Grafana)이 대신하므로 트리에서 제거했다 (git 이력에는 남아 있다).
