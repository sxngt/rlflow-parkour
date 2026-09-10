# P0 착수 기록

2026-09-10 사용자 계획 v1.1을 연구 방향으로 채택했다. P0 전체 완료를 의미하지 않는다.

## 호스트 실측

- Ubuntu 20.04.6 LTS, Intel i9-10900X, 10 cores / 20 threads.
- RAM 약 188 GiB. 작업 볼륨 여유 약 542 GiB, 사용률 93% (착수 시점).
- RTX 4090 4장, 각 24564 MiB, driver 550.144.03.
- 확인 시 GPU 사용률 0%, 기존 작업은 종료하지 않았다.
- Isaac Sim: `/mnt/sdb1/sxngt/isaac-sim-4.5.0`.
- Isaac Lab: `/mnt/sdb1/sxngt/IsaacLab`, v2.1.1, commit `90b79bb2d44feb8d833f260f2bf37da3487180ba`.
- 기존 master-thesis 문서의 로컬 Isaac Sim 5.1 지침과 서버 4.5 지침을 구분해야 한다.
- 초기 제한 세션에서는 `.git`이 읽기 전용으로 노출됐다. Full Access 재개 후 실제 폴더에 Git 저장소를 초기화했다.

GPU UUID:

| 호스트 index | UUID |
|---|---|
| 0 | GPU-414c52b4-fc03-1784-60e1-119f6e2de651 |
| 1 | GPU-ec52eb30-0429-367c-f1f2-4763d1c1a7bf |
| 2 | GPU-ac6118d7-5cea-7f13-d68e-9b8448eee924 |
| 3 | GPU-fdb7f2ab-47b7-d41e-a889-8b33f45740de |

## 최소 구현

- A1 모델 선택 근거와 source 기록.
- 고정 길이 물리 smoke, 정답 발 합력·root state 기록, run 상태·설정/출력 hash.
- 선택적 원본 MP4. GPU smoke 결과는 `artifacts/*/run.json`으로 확인한다.
- smoke의 GPU index 지정은 P0 수동 검증용이다. UUID 할당 broker는 아직 없다.

## 다음 완료 조건

### 재시작 인계 (2026-09-10)

- 사용자가 Full Access로 Codex를 재시작하기로 했다. 새 장기 작업은 시작하지 않는다.
- `artifacts/a1-smoke-001`: 600 physics steps / 3초, 12 joints, 4 feet, 유한한 상태·접촉력 검증 통과.
- `artifacts/a1-video-001`: 같은 물리 검사 + 640×480, 25 FPS, 75 frames, 3초 MP4 검증 통과. 첫 프레임도 직접 확인했다.
- 첫 두 실행은 결과 저장 후 Isaac Sim 종료에서 정체했다. 본 세션이 시작한 PID 156768 / 157122에만 SIGTERM을 보냈다.
- `scripts/smoke_a1.py`는 Kit multiGpu enabled/autoEnable을 명시적으로 끄고, 종료 20초 후 자체 프로세스를 exit 2로 종료하며 `shutdown` 이유를 남기도록 보완했다.
- 최종 재검증: `artifacts/a1-video-002/run.json` 및 `artifacts/a1-video-002.log`. 재개 시 이 결과와 GPU 자원 회수부터 확인한다.
- `SUCCEEDED`는 물리 검사·산출물 성공이며, 프로세스 종료까지는 별도 `shutdown`을 확인한다. GPU 독점 할당은 아직 증명하지 못했다. 첫 실행들은 다른 GPU에도 작은 context 메모리를 점유했다.
- `isaaclab` Python package version `0.41.3`은 설치된 release v2.1.1의 extension version이다. 버전 불일치로 잘못 해석하지 않는다. Torch 2.7.0+cu128, numpy 1.26.0, rsl-rl-lib 2.3.3 확인.
- 이후 우선순위: 단일 GPU context·종료 검증 → T0/T1 목표 발 디딤 계약과 PPO 학습 시작. 전체 플랫폼을 먼저 만들지 않는다.

### 남은 P0 작업

1. A1 평지 모델·관절·접촉·headless 영상 실측.
2. 자산 의존성 hash, 환경 패키지 lock 및 별도 환경 재실행.
3. 목표 발 디딤/관측/행동 계약, T0/T1 지형과 split manifest.
4. 목표 조건부 PPO 최소 학습, checkpoint 저장·새 attempt 재개 및 평가.
5. run 메타데이터 저장과 평가→MP4→조회 수직 통합.
6. 1 GPU / 4 GPU 독립 run 처리량 및 CPU·RAM·I/O 프로파일링.

웹·broker·상시 학습·성능 비교는 후속이다. 기존 논문의 파쿠르 성공 수치를 본 구현의 결과로 보고하지 않는다.

## Full Access 재개 진행

- 사용자가 네 GPU 모두 소유하며 연구에 자유롭게 사용할 수 있다고 확인했다.
- UUID CUDA 매핑 + 별도 graphics index로 GPU 2 단독 배치 확인.
- 전용 worker의 저장 후 process exit와 supervisor의 PID/VRAM 회수 검사를 도입했다. 플러그인 teardown 정체 자체를 고쳤다고 주장하지 않는다.
- T0 정적 발 목표 과제와 PPO 학습, 고정 개발군 평가, 원본 MP4·시간 동기 trace 구현.
- seed 0~3을 100 iterations씩 학습하고 각각 새 attempt에서 400 iterations 추가 재개하는 파일럿 진행.
- 재개 checkpoint의 optimizer·normalizer count·iteration/step 증가·가중치 변경을 확인했다. hash가 틀린 checkpoint는 역직렬화 전에 거부했다.
- 최종 결과와 정확한 검증 범위는 `docs/t0-pilot-results.md`에 기록한다.

## 2026-09-10 순차 과제 및 영상 인계

T0S-v2에서 접촉→발 들기→목표 접촉의 실제 이벤트를 검증하며 네 발을 순차 이동한다. 4 GPU에 seed별 1,024환경, 800업데이트 학습과 최종 평가를 완료했다. seed 0/1은 64/64, seed 2/3은 0/64 완주로 seed 간 편차가 남는다. 자세한 결과는 [순차 과제 결과](t0-sequential-results.md)에 기록했다.

사용자 요청에 따라 기본 평가 카메라를 16대가 보이는 원거리 구도로 변경했다. seed 0의 801–825 업데이트를 실제 학습 영상으로 별도 촬영하고 자동 후속 평가·result 수집까지 검증했다. `result/README.md`가 영상 목록이며 원본은 artifacts에 보존한다. 테스트 11개와 새 실행 11건의 artifact/GPU 회수 감사를 통과했다. 종료 시 GPU compute 프로세스는 없다.

다음 연구 작업은 seed 2/3의 정체 원인과 순차 실행 안정성을 분석한 뒤 지형·도약 과제로 확장하는 것이다. 현재는 평지의 짧은 발 이동이며 파쿠르 완료가 아니다.
