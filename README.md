<h1 align="center">rlflow-parkour</h1>
<p align="center"><b>Unitree A1 사족보행 로봇이 24개의 떨어진 발판을 연속 점프로 건너는 파쿠르 코스를, 강화학습 커리큘럼 50단계를 무인 자동화하여 난이도 25% → 92%까지 끌어올린 연구</b><br>
Isaac Sim 4.5 · Isaac Lab 2.1.1 · PPO (rsl_rl) · Ray Tune · <a href="https://github.com/sxngt/rl-flow">RLflow</a> MLOps</p>

<p align="center"><img src="docs/media/hero.gif" width="720" alt="24-gap parkour course, showcase A: 89% completion"></p>
<p align="center"><sub>쇼케이스 A — 갭 89% · 회전 92% · 경사 86% · 높이 92% · 크기 95% 난이도, 64 에피소드 중 57회 완주(89%). 빨간 점은 표면 위 4단계 착지 계획(큰 점 = 다음 착지 예측).</sub></p>

**TL;DR (EN)** — A quadruped (Unitree A1) learns to traverse a 24-gap discontinuous parkour course (gaps up to 0.70 m, rises ±0.27 m, turns to 50°, tilted pads to 22°) in Isaac Sim. A curriculum of 50 stages / 51 Ray Tune sweeps ran **unattended for 44 hours** through RLflow, lifting course difficulty from 25% to 92% (per-axis) with an **89% completion rate** at the final showcase map. Along the way we root-caused every training collapse to a learning-rate restart on policy fork and replaced uniform difficulty steps with probe-guided per-axis steps.

---

## 결과 한눈에

| | 맵 난이도 (gap / turn / tilt / height / size) | 완주 (64 ep) | 정책 |
|---|---|---|---|
| **쇼케이스 A** | .89 / .92 / .86 / .92 / .95 | **57 / 64 (89%)** | `parkour/v51` |
| 쇼케이스 B | .89 / .92 / .86 / .95 / .98 | 48 / 64 (75%) | trial `e3c085b6` |
| 쇼케이스 C | 균일 .86 | 56 / 64 (88%) | `parkour/v45` |
| 시작점 | 균일 .25 | 57 / 64 (89%) | `parkour/v5` |

<p align="center"><img src="docs/media/curriculum.png" width="820" alt="curriculum progression"></p>

- 코스: `mixed_discrete` 24갭, geometry seed 1. 난이도 축 5개(갭 길이 · 회전각 · 발판 경사 · 높이차 · 발판 크기)를 0~1 분율로 스케일.
- 평가: 동결 정책 · 결정론 · 64 에피소드, 성공 = 마지막 발판에 4발 안착 후 0.2 s 유지. 몸통이 발판에 닿으면 즉시 실패.
- 100% 맵은 미완주(최고 정책이 4번째 이동에서 실패). 여기까지가 정직한 도달점이다.

## 왜 어려운가, 무엇을 알아냈나

<p align="center"><img src="docs/media/cliff-vs-pass.gif" width="720" alt="left: uniform 0.89 map fails at gap 13; right: showcase A passes"></p>
<p align="center"><sub>왼쪽: 같은 정책이 균일 0.89 맵에서는 13번째 갭(0.70 m + 0.18 m 상승)에서 몸통이 착지면에 걸려 64/64 실패. 오른쪽: 축별로 조정한 맵에서는 89% 완주.</sub></p>

1. **"절벽"의 진짜 원인은 지형이 아니라 fork 학습률이었다.** 부모 정책은 adaptive KL 스케줄로 LR이 1e-5까지 내려가 있는데, 자식은 설정값 2e-4로 새 Adam을 시작했다. 첫 PPO 업데이트가 성숙한 정책을 무너뜨려 매 단계 수 M 스텝을 재학습에 쓰고, 4번은 아예 회복하지 못했다. A/B(1024 env, 40 iter): LR 2e-4 → 12 iter 만에 이동 수 3 → 0.1, LR 1.5e-5 → 7 → 13. 해결: `+fork_lr=inherit`.
2. **균일 난이도 스텝은 5축을 한꺼번에 흔든다.** 86% 정책을 축 하나만 0.89로 올리면 41~58/64인데, 5축 모두 0.89면 0/64. 그래서 30초 동결 프로브로 축별 허용 폭을 재고, 견디는 조합만 다음 맵으로 삼는 **프로브 유도 축별 커리큘럼**을 만들었다(단계당 프로브 약 2분, 4 GPU 병렬).
3. **탐색 노이즈는 낮아야 한다.** 86% 이후 `min_std` 0.04가 0.06/0.08을 매 단계 이겼다(EMA 0.72 vs 0.46 vs 0.12).
4. **혼합 지형 학습은 망각을 막지만 최전선을 밀지 못한다.** env별로 다른 난이도 맵을 섞어 학습(`terrain_mix`)하면 쉬운 맵 성능은 유지되지만, 정책이 못 하는 난이도에서는 학습 신호가 생기지 않았다.

<p align="center"><img src="docs/media/footfall-plan.gif" width="560" alt="4-step footfall plan overlay"></p>
<p align="center"><sub>착지 계획 오버레이: 큰 점 = 몸통 운동 외삽 + 기본 보폭으로 예측한 다음 착지점, 작은 점 = 이후 3단계 계획기 목표. 모두 표면 위에 그려진다 (`src/parkour/predicted_footfall.py`).</sub></p>

## 방법

```
[맵 생성] curriculum_maps.build_mixed_discrete_axes(seed, {gap, turn, tilt, height, size})
    │
[학습] PPO (rsl_rl, 105-dim obs → 12 joint targets), 2048 env, 1200 iter ≈ 30 분/GPU
    │   fork: 이전 단계 최고 체크포인트 + fork_lr=inherit + min_std 0.04
[스윕] Ray Tune (RLflow lab-pipeline sweep) — std / LR 배수 / 후보 맵
    │
[평가] 동결 정책 64 ep → 게이트(native ≥ 0.75) → MLflow 레지스트리 candidate → validated
    │
[다음 맵] 30 s 동결 프로브 × (축별 +0.06, +0.03) × 조합 → auto-axes / auto-multi 드라이버
```

- 정책·평가·촬영 코드: `src/parkour/` (`continuous_tracker_task.py`, `policy_fork.py`, `terrain_mix.py`, `predicted_footfall.py`, `media.py`)
- RLflow 진입점: `train.py`, `evaluate.py`, `export.py` (연구 코드를 감싸는 얇은 래퍼), 설정 `configs/*.yaml`, 스윕 `configs/sweep/*.yaml`, 평가 스위트 `eval_suite/*.yaml`
- 캠페인 드라이버: [`rl-flow/tools/parkour_campaign.py`](https://github.com/sxngt/rl-flow/blob/main/tools/parkour_campaign.py) — `stage` / `auto` / `auto-axes` / `auto-multi`
- 실행 방법: [docs/rlflow-usage.md](docs/rlflow-usage.md) · 연구 문서 490편: [docs/](docs/) (인계: [active-research.md](docs/active-research.md)) · 이관 이전 README: [docs/legacy-readme.md](docs/legacy-readme.md)

## 숫자로 보는 캠페인 (2026-09-13 → 09-15)

| 항목 | 값 |
|---|---|
| 무인 진행 | 50 단계 · 51 스윕 · 약 150 trial · 44 시간 |
| 학습 규모 | 단계당 2048 env × 1200 iter ≈ 5.9 × 10⁷ env-step, 총 ≈ 9 × 10⁹ env-step |
| 도달 난이도 | 균일 .86 통과, 축별 .89 / .92 / .86 / .95 / .98 통과 |
| 평가 | 모든 단계 64 ep 동결 평가, 정책 55 버전 등록 |
| 실험 자산 | 콘솔 런 1,456개 (이관 1,378 + 신규 78), 영상 900+ |

모든 런·지표·영상·계보는 RLflow 콘솔(`/p/parkour`)과 MLflow에 있다. 쇼케이스 세 런은 `purpose:showcase` 태그로 모아 볼 수 있다.

## 배경

원본 연구(`workspace/parkour`, 351 커밋)는 사전 지도 기반 Planner–RL Tracker 구조로 단일 도약 → 연속 도약 → 혼합 지형으로 단계를 밟아 왔다. 2026-09-13에 RLflow 프로젝트로 이관하면서 실행 1,375개와 영상 900개를 무수정 임포트했고, 이후의 모든 학습·평가는 RLflow를 통해 이루어졌다. 구현은 AI 코딩 에이전트(Claude Code)와 페어로 진행했다.
