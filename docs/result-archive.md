# 실행별 최종 평가 영상 보관 규칙

사용자 요청(2026-09-10): 각 실행 단위의 최종 평가 영상을 `result/`에 별도로 정리하고 자세한 제목을 붙인다.

## 자동 처리

정상 종료한 `scripts/run_job.py ... train`은 해당 attempt의 최종 checkpoint로 별도 평가 프로세스를 실행한다. 고정 개발군 64개를 평가하고 고정 4×4 구역의 16개 로봇을 1280×720, 25 FPS 원본 MP4로 촬영한다. 평가 종료와 GPU 회수 확인 후 영상·평가·시나리오·replay를 `result/`에 복사하고 SHA-256을 검증한다.

- 학습 실행: `artifacts/<run>/`
- 최종 평가 실행: `artifacts/<run>__final-evaluation/`
- 보기 좋은 목록: `result/README.md`
- 상세 폴더: 날짜 · A1 · 과제 버전 · seed · 업데이트 수 · 평가 실행 ID
- MP4 제목: A1 · 과제 설명 · 정책/대조군 · seed · 업데이트 수 · 병렬 로봇 수 · 최종 평가 (기존 단일 영상은 시나리오와 종료 결과)

학습과 평가는 별개 상태다. 학습이 성공했더라도 평가나 영상 수집이 실패하면 명령은 실패를 반환하고 원인을 표시한다. 이미 저장한 학습 checkpoint를 지우거나 학습 실패로 바꾸지 않는다. 재평가는 새 출력 경로로 실행하면 된다.

학습 `--timeout`은 학습 worker 예산이다. 후속 평가에는 별도로 최대 180초 예산을 부여한다. 디버그·자원 프로파일링에서 평가를 생략하려면 `train` 앞에 `--skip-final-evaluation`을 명시한다. 이 변경 이전에 시작한 기존 학습 작업은 수동 최종 평가로 연결했다.

## 수동 복구·기존 결과 편입

```bash
python3 scripts/collect_results.py artifacts/<evaluation-run>
```

이미 있는 동일 평가·동일 영상 hash는 중복 생성하지 않는다. 손상된 파일이나 충돌하는 결과는 덮어쓰지 않고 오류로 표시한다. 여러 GPU가 동시에 평가를 마쳐도 파일 lock으로 목록 갱신을 직렬화한다.

## 해석

전체 평가 성공률과 영상 한 편의 결과는 별개다. 새 영상은 성공 사례를 선별하지 않고 고정 4×4 구역을 촬영한다. 기존 단일 영상은 고정 개발군 첫 시나리오다. 먼저 끝난 환경의 자동 reset이 보일 수 있지만 전체 통계에는 각 환경의 첫 episode만 포함한다. 순차 과제는 평균 완료 접촉 수와 영상의 완료 접촉 수를 함께 표시한다. 정확한 원본·모델 hash·학습 실행은 각 폴더의 `manifest.json`에서 확인한다.

100회 학습의 좋지 않은 결과도 이전 attempt의 최종 평가라는 점을 명시해 보존한다. 중단되어 유효한 최종 모델이 없는 실행을 성공 영상으로 포장하지 않는다. `result/`는 로컬 산출물 폴더로 Git에서 제외하며, 원본 `artifacts/`와 함께 보존한다.

## 실제 병렬 학습 촬영

`train --video`는 PPO rollout과 가중치 업데이트를 실제로 수행하면서 1,024개 환경 중 고정 16개만 화면에 표시한다. 나머지도 물리 시뮬레이션과 학습에 참여한다. 렌더링 비용 때문에 일상 학습은 headless로 두고 짧은 별도 attempt를 녹화한다.

```bash
python3 scripts/run_job.py --gpu 0 --timeout 300 train \
  --config configs/t0-sequential-ppo.json --out artifacts/my-training-video \
  --seed 0 --iterations 25 \
  --resume artifacts/t0s-v2-seed0/checkpoint-000800.pt --video
```

실제 촬영한 seed 0의 801–825 업데이트 영상은 300 frames / 25 FPS = 12초다. 이는 simulator 시간이며 실행 wall-clock과 다르다. 자동 최종 평가 후 같은 result 폴더에 **실제 병렬 학습**과 **최종 평가** 링크가 각각 생성된다. 병렬 trace에는 simulator 시간, 표시 환경 ID, 몸체·발 위치, 목표 및 접촉 진행 단계가 포함되며 학습 trace에는 업데이트 번호도 기록한다.
