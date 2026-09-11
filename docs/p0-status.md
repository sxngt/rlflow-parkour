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

## 2026-09-10 모니터링 웹 인계

FastAPI + React/TypeScript/ECharts + 별도 PostgreSQL 색인으로 조회용 모니터링 웹을 구축했다. run 45건·평가 영상 묶음 14개를 연결했으며 GPU/호스트 자원·학습 지표·로그·파일·영상/replay를 조회한다. 웹은 http://127.0.0.1:18710 및 Tailscale http://100.104.103.77:18710. `parkour-monitor-{db,collector,web}` user systemd 서비스가 운영 중이며 linger가 활성화돼 있다. 전체 설치·검증·제약은 [웹 운영 문서](monitoring-web.md)를 따른다. 실행 제어 API나 장기 scheduler는 이번 조회용 웹과 별도다.

## P1 Step 01 진단·phase 태그 인계

기존 800-update seed 0–3 및 zero 대조군을 200Hz에서 계측했다. 결과는 `docs/hopping-diagnosis-results.md`, 재생 영상은 result. seed 1은 64/64에서 연속 20ms 이상 네 발 무접촉, seed 0은 0/64이며 두 모델 모두 64/64 완주한다. 4개 seed의 evaluation.json은 계측 이전과 완전히 같다. 보상/정책 변경은 아직 하지 않았다. 다음은 별도 버전의 지지·착지 기준과 동일 예산 보상 비교다.

웹은 Phase·실험 단계·과제·목적 태그로 실행·영상·원본 파일을 검색한다. `configs/research-tags.json`이 표시 이름과 과거 분류 registry이며 새 실행은 config/run에 태그를 남긴다. 현재 본 진단은 P1 + step:01-hopping-diagnosis + purpose:diagnosis (5건). 계측 파일럿 1건은 별도 purpose로 보존한다. API/웹 서비스는 기존 공인 18710 포트. SSE 연결이 있어도 재시작이 끝나도록 graceful shutdown 대기를 3초로 제한했다.

## P1 Step 02 결과 인계

사전 프로토콜 `docs/step02-protocol.md`에 따라 v3 과제(다른 3발 지지 이벤트 + 최종 0.2초 안정화)를 정의하고 수직 속도 벌점 A=0/B=4를 seed 0/1, 1024환경×800updates씩 처음부터 학습했다. 총 78,643,200 환경 steps. 4 run 및 자동 최종 평가/진단/영상 수집 완료, 자원 해제와 hash/계보 검사 8건 통과.

모든 조건에서 안정화 포함 완주 0/64, 4발 이동 완료 0/64. 평균 완료 접촉 A0=.9531, A1=1.9844, B0=.9063, B1=2.0. B의 수직 속도 RMS는 낮지만 진행 개선은 입증하지 못했다. 대부분 두 번째 발 착지 또는 세 번째 발 들기에서 정체한다. `docs/step02-results.md`, `docs/step02-summary.json`에 자세히 기록했다. 실패를 보존하고 모델 승격은 하지 않았다. 다음은 발별 단일 이동 능력과 3발 지지 조건을 분리한 커리큘럼 파일럿이다.

웹은 P1 / 02·발 디딤 기준선 / 목적: 조건 비교 / 실험 조건 A·B로 검색한다. 비교 화면은 필터 범위의 학습을 선택하며, 평가의 scenario seed 10000과 학습 모델 seed를 구분하도록 수정했다. 구현 확인 3,072 steps와 합성 상태 전이 검사는 목적: 구현 검증으로 별도 분류한다.

## P1 Step 02a 발별 단독 이동 결과 인계

v4는 지정 발 1회 착지 후 기존 stage 4 안정화로 이동하며 다른 발 목표를 유지한다. FL/FR/RL/RR 각각 seed 0, 1024환경×800updates로 학습(총 78,643,200steps), 64개 고정 개발군 평가·200Hz 진단·16대 MP4를 완료했다. 네 조건 모두 착지 64/64, 안정화 성공은 FL 0/64, FR 64/64, RL 0/64, RR 4/64. 낙상은 없고 나머지는 timeout이다. RL은 2/64에서 ≥20ms 전 발 무접촉이 있어 이벤트 지지 조건만으로 hopping 제거를 주장하지 않는다.

최종 지지 발 오차가 안정화 기준을 넘는 조건들이 남는다. 다음은 기존 보상 대조군과 지지 발별 오차/최종 정렬 신호를 명시한 변경을 동일 예산·추가 seed로 비교하는 후보이다. 아직 변경 효과나 순차 실행 성공을 주장하지 않는다. 보고서 `docs/step02a-results.md`, JSON `docs/step02a-summary.json`; 원본 `artifacts/p1-step02a-single-{fl,fr,rl,rr}-seed0` 및 `__final-evaluation`. 영상 4개는 상세 발 이름 제목으로 result에 보존한다.

태그 P1 / 02a·발별 단독 이동 / 발별 조건으로 실행·영상·파일 조회. 웹과 결과 목록의 완료 접촉 분모는 required_contacts(이번에는 1)를 사용한다. evaluation manifest에 실제 task와 sequence_contract를 기록한다. 학습 코드·예산 고정 commit ccb4167, 이후 c0af055는 평가 메타데이터/보고서만 변경했다. 합성 상태 전이 검사 통과, 단위 15개·모니터링 6개 통과, 8run artifact/GPU 감사 통과.

## P1 Step 02b 최종 정렬 벌점 비교 인계

사용자의 즉시 후속 학습 지시에 따라 최종 단계에만 네 발 XY 정렬 비용을 추가하는 B(v5)를 A(v4)와 비교했다. FL/RL × seed 0/1, 각 800updates. A seed0 두 run은 02a 원본 재사용. 신규 6run = 117,964,800step, 전체 비교 예산 = 157,286,400step. 사전 프로토콜·학습 코드 고정 commit 5ae5c1b. 보상은 최종 단계에서만 `-mean(min((XYerror/.025)^2,16))*dt` 추가, 성공 기준은 동일.

A는 FL/RL 모두 seed0 안정화 0/64, seed1 64/64. 모든 A 착지 64/64. B 네 run은 모두 착지/안정화 0/64이며 낙상 없이 timeout. B FL seed0/1·RL seed0은 착지 단계, RL seed1은 들기 단계 정체. 비용을 피하는 양상과 일치하지만 물리 원인이나 정책의 의도를 확정하지 않는다. B는 채택하지 않는다. 기존 보상의 seed 변동이 커 추가 seed 검증이 필요하다. 다음 후보는 단계 진입을 불리하게 만들지 않는 오차 개선 신호와 기존 보상의 재현성 확인이며 아직 구현하지 않았다.

`docs/step02b-results.md`, summary JSON, 학습 그림에 결과 기록. `artifacts/p1-step02b-*` 학습 6건·최종 평가 6건, 상세 제목 MP4 6개를 result에 보존. 태그 P1 / 02b·최종 네 발 정렬 / A·B / FL·RL로 검색. 재사용 A0는 registry override로 이번 비교에도 연결하고 원본 artifact는 변경하지 않았다.

신규 12run hash·계보·UUID·GPU 회수 감사 통과. 단위16개/모니터링6개/합성 상태 검사 통과. 모든 작업 종료 후 GPU compute 프로세스 없음. champion 승격은 하지 않았으며 다음 실험은 미실행.

## 상시 연구 목표 활성화 · Step 02c 및 02d 인계

사용자가 잠든 동안 중단 지시 전까지 계속 연구하라고 명시했다. goal active이며 실험→평가→다음 판단을 지속한다. 자동 champion 승격은 하지 않고 원본·영상·실패를 보존한다.

02c C(v6)는 B(v5)의 정렬 비용을 전 단계에 적용했으나 FL seed1 착지9/64, 나머지 착지0/64, 모두 안정화0/64. 신규4학습·4평가 감사 통과, 영상4개 result 저장. C도 채택하지 않았다. 보고서 docs/step02c-results.md와명세configs/reports/step02c.json. 코드6f02321.

02d는 기존A(v4)의 FL/RL seed0/1을 800 checkpoint에서추가800updates재개 중이다. GPU0 FL0, GPU1 RL0, GPU2 FL1, GPU3 RL1. run artifacts/p1-step02d-a-{fl,rl}-seed{0,1}, launcher로그 같은접두. 원본seed0은02a single, seed1은02b A. 신규run끝update1600, 추가예산78,643,200step. 프로토콜docs/step02d-protocol.md, report명세configs/reports/step02d.json, 고정commit4f8383c.

다음행동: 네run과자동평가·MP4·result완료까지확인, scripts/audit_artifacts.py감사, Isaac python으로scripts/experiment_report.py configs/reports/step02d.json실행. 결과분석후다음실험을계속진행. 보고서 helper는attempt_environment_steps와누적environment_steps를분리해재개예산중복계산을피한다. 아직02d결과를보고하지않음.

## Step 02d 완료 · 공유 Tracker 다음 단계

02d 재개4run은누적1600updates 완료. 고정평가 안정화 FL0=0/64, FL1=64/64, RL0=64/64, RL1=64/64. 모두착지64/64. RL0는800update의0/64에서개선됐고 기존성공seed1은유지됐다. FL0는최종안정화에서정체. 모든재개평가 ≥20ms전발무접촉0/64. 신규8run감사통과, 영상4개result등록. 보고서docs/step02d-results.md 및configs/reports/step02d.json. 신규78,643,200step으로 실제비교총157,286,400step. 모든학습·평가프로세스종료와GPU회수확인.

다음은02e 공유단독발Tracker. 사전프로토콜docs/step02e-protocol.md만 작성했고 아직코드/학습미실행이다. 한정책이episode마다균등활성발을처리하도록환경별foot order를도입할계획. 기본A보상유지, 추가정렬벌점없음. seed0~3,1024env×1600updates,평가256개(각발64)·16대영상. 현재코드의order는global1D라서그대로randomize하면안된다. active_feet helper와Nx4 episode_order 등을통해관측·목표·접촉이벤트·진단·영상의활성발을같이갱신하고, 평가명세의활성발을reset이후명시적으로적용해야한다. 기존v2~v6고정순서회귀검사와random reset독립성검사필요.

평가episodes는run_job.py의자동평가명령이기본64이므로config의evaluation_episodes=256을전달하는확장이필요하다. shared평가레코드에활성발을남기고발별집계한다. scripts/experiment_report.py는현재foot='FL'/'RL'를전제로최종오차계산하므로shared task에맞게확장하거나별도report를작성해야한다. goal은active이며사용자중단전까지계속연구한다.

## Step 02e 구현 및 학습 시작

공유 Tracker v7 구현 commit2363c8a. SequentialEnv에 환경별 episode_order(N×4)와 active_feet()를 도입했다. 고정 과제는 기존 순서 반복으로 유지하고, v7은 reset된 환경만 균등 첫 발 선택 후 순서를 회전한다. 관측·접촉이벤트·목표·진단·영상 모두 같은 환경별 활성 발을 사용한다. 평가 명세는 활성 발/순서를 명시하고 reset 후 목표와 함께 재적용한다.

사전 검증: 합성 active/target/reset독립성/최종stage 검사 PASS, 단위18개·모니터링6개·웹빌드 통과. 이전 FL seed1의 1600update 고정평가 재실행 p1-step02e-fixed-regression의 evaluation.json은 원본과 완전히 같다. p1-step02e-shared-zero-check는256개/각발64개 zero평가·200Hz진단·16대영상·result수집 완료. 두run GPU/hash 감사통과, 구현검증태그로학습비교에서제외.

4개 공유정책 학습 실행 중: artifacts/p1-step02e-shared-seed{0,1,2,3}, GPU index=seed.1024env×1600updates 처음부터, 각39,321,600step. supervisor timeout1800s, 자동최종평가에는config evaluation_episodes=256을전달하고 timeout180s. 사전zero평가48.8초로경로검증. 실행 shell tool session14927/46890/66762/16366; 새턴에서는process/실제GPU확인후관측한다.

다음행동: run 종료 및 자동256평가·영상·자원회수 대기, audit_artifacts.py로8run검사. Isaac python scripts/experiment_report.py configs/reports/step02e.json로발별보고서를생성한다. helper는foot=ALL일때시나리오별active_foot으로target오차계산하고by_foot 성공/착지/무접촉을표시한다. 학습도중설정변경없이, 결과에따라공유정책실패분석/순차연결로진행. 아직02e학습성과없음. goal active 유지.

## Step 02e 결과 및 P2 준비 인계

공유정책1600updates seed0~3 학습/256개평가 완료. 안정화 성공0/190/127/192(각256중), 착지완료61/256/128/256. 발별성공(FL,FR,RL,RR): seed0=(0,0,0,0),seed1=(62,64,0,64),seed2=(63,0,0,64),seed3=(64,64,64,0), 각발64개. 모든평가≥20ms전발무접촉0. seed1/3은모든발착지64/64이지만각각RL/RR최종안정화실패. 공유제어기의부분실행가능성은확인했으나전발재현성은미확보이며승격없음.

신규8run artifact/UUID/자원회수감사통과. 최종영상4개result등록. scripts/experiment_report.py의NPZ반복압축해제병목을고쳐필요배열을한번씩만읽는다. docs/step02e-results.md,summaryJSON,configs/reports/step02e.json에발별결과·종료단계·오차를남겼다.

다음은P2최소도약계약검사. 정적3발지지모든seed완벽성을원래파쿠르목표대신최적화하는분기를계속늘리지않는다. docs/p2-transition-review.md를읽고진행. 기존P1은한계와실패를보존하며전체P1검수완료를주장하지않음.

현재UNITREE_A1_CFG는self_collisions=False,토크/포화33.5Nm,속도21rad/s. FootholdEnv의failure는trunk접촉만사용하지만MotionDiagnostics는비발전체netforce를기록한다. 동적새과제에서selfcollision켜기/기본자세·접촉관측검증,비발접촉실패명세가우선이다. 내부접촉을netforce만으로완벽히분리할수있는지확인하고검증한범위만주장한다. 구동기한계는늘리지않는다.

P2제안(아직미구현/학습미실행): 평지의명시적단일도약부터실제전발비접촉지속과몸체상승/속도를확인한뒤착지·안정화. 다음에수평이동·제한착지면·단일갭확장. 3발지지정적조건은이새동적과제에강제하지않는다. 비행이없는서기/개별발들기는점프성공아님. observation·phase·contactgroup·media/diagnostics/report계약을새버전으로분리하고합성상태검사후수치/예산사전고정. 공유Tracker를더재개하지말고목표연구로진행한다.

목표active,사용자중단전까지지속. 현재학습/평가worker전부종료,4GPU회수완료.

## P2-00 충돌 계약 검사 완료

collision_probe.py를추가하고run_job.py의명시적kind allowlist에collision_probe를추가했다. 두64env프로브 artifacts/p2-00-collision-{off,on} 완료. 실제USD articulation selfcollision flag 일치 확인. 정상1초지지의비발>5N은양쪽0/64,body-ground overlap은양쪽64/64. 지상3m randomjointpose 50ms는off0/on1 비발접촉, 같은샘플pose확인. 양성case47의FL_thigh43.37N,RL_calf7.66N,RL_foot35.71N. 모든bodycenter>2.64m로ground접촉분리. netforce만으로모든pair충돌검출을주장하지않음. docs/p2-collision-contract.md에결과/한계기록.

새동적과제는selfcollisions=True와nonfoot전체합력>5N실패를사용할계획이며기존P1은그대로둔다. 모터33.5Nm/21rad/s/PD25,.5유지. scripts/audit_artifacts.py는probe kind의hash감사를추가했고두probe UUID/회수/hash통과. 현재4GPU모두비어있다.

다음은P2단일도약환경구현(아직미실행). 평지에서명시적비행과착지검증부터진행하고수평이동/갭으로확장. 제안설계: 보정된기본자세로reset,초기settling이후전발합력비접촉의physics history(200Hz)와몸체상승을함께확인해flight latch,이후접촉재개와최종4발안정화구분. 비발접촉history>5N은실패. root/base높이를COM이라고부르지않는다. 발만들거나높이만높인서기는flight없어성공불가. 숫자/예산은합성검증후학습전고정.

구현주의: 별도JumpCfg/Env/ task/version 필요. 현재v7 active_feet와phase관측은개별발에특화돼있으므로그대로점프에적용하지않는다. 새all4contactgroup에맞는관측(기본61+phase/명령/시간),media의phase label,diagnostics의support mask,평가 KPI(비행/apex/착지/안정화),scenario generator/registry/restore계약을분리한다. 기존결과는소급변경금지. GPU1~4상태검사후소규모synthetic/zero계약검증을먼저수행할것. goal active이며계속진행.

## P2-01 단일 도약 환경 검증 및 본 학습 시작

JumpEnv/JumpCfg, jump_events.py를 추가했다. self-collision on, 비발전체history>5N실패,66차원관측,기존모터/PD/±.5rad행동. 초기.3초PD유지 후 최근4물리표본 전발합력<2N + 몸체상승≥.03m + 상승속도≥.2m/s로유효비행을한번검출한다. 확인된비행/비접촉중apex가요구4–6cm이상이어야하고,비행후접촉4개와5cm목표반경·.2초안정화로성공한다.4초truncation,정지성공불가. 상세수식/예산은docs/p2-01-protocol.md.

초기cfg class속성참조오류를수정했다. artifacts/p2-01-jump-state-check-v2.log의합성검사는관측66/서기거부/상승비행검출/공중성공거부/최종hold PASS. 단위23개/모니터링6개/웹빌드통과. zero64개평가(유효비행0,성공0) 및64env×2update=3072step 구현확인과자동평가/200Hz진단/MP4/result수집완료. artifacts/p2-01-jump-zero-check 및p2-01-jump-implementation-check, __final-evaluation. 이3run감사PASS,구현검증태그로본학습예산제외.

본학습4run 시작: artifacts/p2-01-jump-seed{0,1,2,3}, GPU index=seed.1024env×1600updates 처음부터,신규총157,286,400steps. supervisor1800초,자동64평가/영상/진단. 현재학습handle16513/82355/43896/91666. 학습계약bb94ad6 후unused단독발메타데이터정리5500f4b,보고서등록0f8a3a5로실행.

단일활성발이없으므로JumpEnv.active_feet()=-1,contact_group_all=True. media는4개목표모두표시하고phase_labels(도약준비/비행/착지안정화)를저장한다. 웹도이label을사용한다. diagnostics는grouped task에서지지중모든발의XY이동을집계하며active=-1을개별발로해석하지않는다. 유효비행은별도event계약이고기존diagnostic의≥20ms무접촉통계와같지않다.

다음행동: 실제프로세스/메트릭으로4run을관측하고완료후자동평가·영상·GPU회수를확인한다. audit_artifacts.py 8run검사,Isaac python scripts/experiment_report.py configs/reports/p2-01.json로보고서생성. report helper는required_contacts4에맞추고valid_flights/landed_episodes/비발접촉/meanapex를별도표시한다. 결과로보상악용·상승/비행/착지실패를분리해다음학습을결정한다. 수평이동/제한착지면/갭은아직없고본실험은평지작은도약이다. goal active 유지.

## P2-01 완료: 작은 비행은 획득, 높이·착지 안정화 미달

4seed×1600updates 및 각64개 평가 완료. 모든 seed 유효 비행/네 발 재접촉64/64, 성공0/64, 비발 접촉 종료0, 모두시간초과. 비행 apex 평균3.75/4.41/4.43/4.43cm, 요구높이 충족0/11/11/12개. 최종 몸체는 보정 자세보다10.10/8.16/8.16/8.76cm 낮아 모든 episode가±6cm 높이 조건을 벗어났다. 첫 접촉 네 발 모두5cm 이내는 전seed0/64이며 나중의 작은 발오차를 정밀 착지로 부르면 안 된다.

8run UUID/lease회수/checkpoint·영상·진단hash감사통과(artifacts/p2-01-audit.jsonl). result에최종영상4개보존. docs/p2-01-results.md,summary,height-diagnosis,figures의결과 및 scripts/p2_01_trace_report.py로진단재생성. 200Hz 첫접촉 지표는학습시작후추가한보조지표이며원래성공계약은그대로다. tests24통과.

다음은P2-02 보상 수정: 유효비행 후 요구apex까지의1회성 진행 보상, 착지 후 몸체 높이 비용을 결합한다. 성공 조건·구동기·명령분포·예산은유지하고기준선4seed와비교한다. 두항개별기여를분리한주장은하지않음. 먼저순수함수검증/짧은시뮬레이터경로검증. 모델승격없음. 현재4GPU회수완료. goal active,사용자중단전까지계속진행.

## P2-02 본 학습 실행 인계

P2-02 구현 및 검증 완료, 본 학습4개 실행 중. 새task a1_flat_jump_shaped_v2, 보상 추가분은 episode당 최대3의apex 진행도 증가와 착지 후 높이 정규화 제곱 비용0.5×dt(상한초당2). 성공/실패/명령/관측/구동기/PPO 조건은동일. docs/p2-02-protocol.md 사전고정. 두항결합효과만주장하며개별기여는미분리.

단위26개통과, 실제시뮬레이터 합성검사에서서기거부/유효비행/공중성공거부/진행도포화·중복보상방지/최종hold통과. artifacts/p2-02-jump-state-check.log. 별도64env×2update,64평가+MP4+200Hz+result 및2run감사완료: artifacts/p2-02-shaped-implementation-check, __final-evaluation. 구현확인성공0/유효비행0이며본예산제외.

본4run artifacts/p2-02-shaped-seed{0,1,2,3}, GPU index=seed. 각1024×24×1600updates=39,321,600step,총157,286,400신규. 현재shell tool session42486/7314/10665/2176;4run RUNNING 실제update7–12확인. 실행commit d720f20. supervisor1800초,최종64평가자동영상/진단180초. 기다리는 동안실제메트릭/프로세스확인하며중복실행하지말것.

다음행동: 종료/자동평가/자원회수 후8run감사, configs/reports/p2-02.json로보고서생성. 명세는P2-01의4seed를재사용A로포함하고새4seed를B로비교(총314,572,800step,신규절반). 첫접촉/요구높이충족/최종높이를별도확인. 기존P2-01영상/원본config는변경하지않고catalog override에P2-02대조군태그추가. API runs/videos200확인. 보조지표는사후진단이며시험군주장안함. 모델승격없음. goal active 유지,사용자중단전까지연구계속.

### P2-02 실행 중 보고서 보완

실제 GPU worker PID666799/666892/666997/667095를 확인했다. 4run은 update238–242까지 진행 중이며 종료 episode의 apex 명령 충족은 증가했지만 성공은 아직0. 이것은 중간 학습 통계이며 최종 평가 결과가 아니다. 기존 session42486/7314/10665/2176을 유지하고 새 실행을 만들지 않는다.

scripts/experiment_report.py의 jump 표에 조건명(A/B)과 마지막 유효 표본의 높이 범위 위반 수를 추가했다. docs/p2-01 결과를 다시 생성해 기존 높이 진단 수치와 일치 확인. scripts/jump_trace_report.py configs/reports/p2-02.json은 평가 완료 후 조건별 동일 대표 명령의 높이/발오차 궤적을 생성한다. 각episode의 valid 마지막 표본을 사용하므로 성공 조기 종료·auto-reset 데이터가 최종높이에 섞이지 않는다. 기존 p2_01_trace_report.py는 호환 실행기로 유지한다. P2-02 종료 후 report와 trace report를 모두 실행할 것.

### P2-02 중간 관측 및 정확한 종료 조건 기록

4개 실제worker PID666799/666892/666997/667095가 살아 있고 update514–527까지증가했다. 평균 최종발오차약1–2cm,성공0이며고정예산유지. GPU33–34°C/약3GB씩,디스크540GB여유. 완료나최종성능으로해석하지않는다.

commit2d5203f는평가에final_height_error_m/final_vz_m_s/final_angular_speed_rad_s/final_contact_all/final_supported/final_all_feet_in_radius를추가한다. diagnostics에root_xy/root_angular_velocity_b도추가. 제어·보상·종료논리는동일하고진행중학습프로세스는이미로드한기존코드대로실행된다. 자동최종평가가새commit의기록필드를저장한다. report는존재하는필드만위반수집계하며과거실행누락필드를추정하지않음. 마지막표본위반과전체hold실패원인은구분. py_compile/diff검사통과,실제새필드출력은자동평가완료후확인필요.
