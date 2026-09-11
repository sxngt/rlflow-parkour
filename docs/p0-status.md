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

## P2-02 완료: 네 seed 안정화 성공, 첫 착지 정밀성은 미달

4개1600updates 및각64평가완료. A=P2-01모든seed0/64 → B=P2-02모든seed64/64. 유효비행/apex명령충족/네발재접촉전부64/64,최종높이·수직속도·각속도·목표반경·접촉상태·history위반전부0. 비행apex평균5.7/6.3/7.6/6.1cm,최종높이보정자세대비-1.30/-0.61/-0.37/-0.55cm. 작은평지명령개발집합에서의도약후안정화성과로범위제한. 정밀apex추종/외란/갭/최종시험주장안함. 모델자동승격없음.

하지만첫접촉네발모두5cm내는A/B전seed0/64. B발별첫접촉오차최대값의episode평균13.1/21.1/7.0/10.4cm. 최종정렬과첫착지는다르다. 다음은P2-03 첫착지정밀화이고이후수평목표/제한착지면/갭확장. P1정적문제를다시끝없이최적화하지않는다.

artifacts/p2-02-audit.jsonl의8run감사통과,4GPU실제compute프로세스없음/회수완료. result에4최종MP4등록. docs/p2-02-results,summary,height-diagnosis,figures생성. 종료조건추가기록의실제출력확인. scripts/experiment_report.py 및jump_trace_report.py configs/reports/p2-02.json로재생성. 현재학습worker없음,새P2-03검증준비중.

src/parkour/first_touch.py 순수torch FirstTouch 모듈과tests/test_first_touch.py를추가했다. flight_seen 이후최초합력>5N의발중심XY를발별고정. 비행전/정확히5N은제외,두번째접촉/후속보정으로오차덮어쓰지않음,일부env reset격리.27단위검사통과. 아직시뮬레이터에연결하지않았고새정책학습은미실행이다.

다음구현제안: 별도PrecisionJumpEnv가JumpEnv를상속하고scene.update를감싸각200Hz물리갱신직후FirstTouch.update를호출. 기존MotionDiagnostics도scene.update를감싸므로기존wrapper를먼저호출해순서를보존한다. localXY=body_pos-env_origin,targets는world기준이므로동일frame변환필수. parent __init__ stancecalibration후hook설치,reset시FirstTouch초기화. _pre_physics_step에서보상누적buffer0,각physics첫접촉만bonus누적. 최초비행latched이후만작동하므로기존사후진단stage>=1과대조가능하다. IsaacDirectRLEnv.step은physics scene.update4회→episodecounter증가→dones→rewards→reset→observations순서임을로컬코드확인했다.

성공계약제안: 기존안정화성공 AND first_touch.within(.05). 기존안정화달성은별도latch해보고,새엄격성공과기존성공을혼동하지않는다. 목표밖첫착지후보정은새성공불가. 보상제안은기존v2를유지하고첫접촉위치bonus(예:2*exp(-error/.08),발별1회)를추가; 아직고정/실행하지않았으므로프로토콜을먼저확정하고검증할것. 명령분포는우선기존평지목표,새4seed고정예산비교. 공통첫접촉지표로기존모델과비교해야하며새성공률을기존성공률과동일계약처럼비교하지않는다. 합성정확/잘못된첫접촉·이후보정거부·reset검사,짧은학습/평가/200Hz일치검증후본학습. goal active 유지.

## P2-03 첫 착지 정밀화 구현 및 본 학습 시작

PrecisionJumpEnv(별도task a1_flat_jump_precise_v3)를구현했다. scene.update wrapper가원래update후200Hz힘/발위치를읽고FirstTouch에저장. 세계좌표발/목표를동일env-localXY로변환. 첫접촉bonus=2*exp(-error/.08),발별1회/episode최대8,실패표본추가보상0. 기존v2보상유지하되+8성공은기존hold AND네발첫접촉≤5cm에만지급한다. 잘못된첫접촉후보정은새성공불가,기존stabilized_once는별도latch. first_touch_error_{fl,fr,rl,rr}_m 미접촉은-1.66차원관측은그대로라모든과거사건을관측하는Markov상태라고주장하지않음.

단위27개,합성시뮬레이터scripts/check_precision_jump.py PASS: 서기거부/잘못된firsttouch후안정화성공거부/실제physics접촉읽기/bonus1회/정확한첫접촉hold. artifacts/p2-03-precision-state-check.log. 구현확인64env×2updates 및64평가/영상/진단/2run감사PASS(artifacts/p2-03-precise-implementation-check, __final-evaluation). 짧은정책유효비행0/성공0이므로report에서온라인firsttouch와원본일치는누락값만검증. 본학습평가에서양성접촉일치추가검증필요.

본학습4run시작: artifacts/p2-03-precise-seed{0,1,2,3},GPU index=seed. 각1024×24×1600업데이트39,321,600step,총157,286,400신규. 실행commit f80700a. supervisor1800초,최종64평가영상/진단자동. shell session83363/49250/59692/24997. 시작후실제PID/메트릭확인필요. 실행중설정수정/중복재시작금지.

configs/reports/p2-03.json은A=P2-02재사용4seed,B=P2-03새4seed. 새성공계약차이를제목/표에명시하고공통첫접촉비율·stabilized_once로비교한다. report helper는발별온라인firsttouch와사후200Hz오차1e-5m이내일치assert. count누락은-1/None매칭. 이전A의첫접촉은모두실패(전seed0/64)지만기존안정화64/64였다. 따라서새B0성공을A64와동일기준처럼해석하면안됨.

다음은실행상태관측→자동평가/회수→8run감사→experiment_report.py와jump_trace_report.py configs/reports/p2-03.json→실패분석/후속학습. 최종영상은T1J-v3상세제목result등록. P2-02대조군에catalog override로P2-03태그추가,원본config불변. goal active 유지.

## P2-03 완료: 첫 접촉은 정밀해졌으나 지지 안정화 부족

네1600학습및각64평가완료. 새엄격성공0/8/0/0, 기존안정화달성stabilized_once도0/8/0/0. 공통첫접촉네발5cm내는전seed64/64(P2-02대조자료는전seed0/64). 온라인FirstTouch의발별양성값과원본200Hz사후오차가전부1e-5m이내일치. 발별평균첫오차약0.03–0.49cm. 새모델승격없음. 새로운수평목표나갭일반화는아직없다.

마지막접촉상태위반64/35/64/58,history위반64/47/64/63. 높이/XY위반0. 착지단계200Hz 네발>5N비율0.15/28.30/0.58/8.83%,vzRMS .055/.127/.171/.209m/s,네발<2N비율0/12.09/1.64/32.72%. seed0은전발재비행이없으므로단순hopping만문제로보면안됨. 일부발지지누락과다른seed수직진동/재비행을분리한다. 기록된후반stage를사용하는보조진단이고최종hysteresis/history판정과동일통계는아님.

artifacts/p2-03-audit.jsonl의8run감사통과,4GPU실제compute프로세스없고회수완료. result의T1J-v3최종영상4개등록. docs/p2-03-results,summary,height-diagnosis,figures생성. configs/reports/p2-03.json로재생성. experiment_report.py에발별최초접촉오차/반경내수/관측수및착지후접촉·vz통계추가. 첫오차의평균분모는관측값,성공분모는모든episode임을명시했다.

다음P2-04: 같은PrecisionJumpEnv/성공계약을유지하고착지이후에만지지부족및수직속도비용을추가하는결합수정. 제안계수support1.0*(1-contact_count/4),vz2.0*vz²에dt곱함. 이계수는아직프로토콜미작성/미구현/미실행이므로실행전고정할것. flight_seen만으로걸지말고landed이후만적용,도약상승자체벌하지않음. 원래firsttouch보상/반경/hold/force임계값그대로. seed0은vz이미작으므로vz단독수정으로모든실패를설명하지않는다. 두항개별기여는미분리결합수정으로표현. 새task/version/config로기록,기존taskweightsdefault0 유지.

구현힌트: jump_events.py의순수함수로landed mask* (supportweight*(1-contact_on.float().mean(dim=1))+vzweight*vz.square()), JumpEnv._get_rewards dense에서차감가능. v4 PrecisionJumpEnv선택라우팅/collect_results/tag/report추가. 순수단위검사(비행중0/완전지지정지0/결손접촉/수직양음동일)/합성검증/짧은train-eval진단hash확인후4seed×1600updates 고정예산. 보고서는P2-03을재사용대조군으로삼되이제엄격성공계약은동일하다고명시. 새첫착지개선을유지하면서안정화회복되는지관찰. 현재새학습없음,goal active 유지.

## P2-04 지지 안정화 본 학습 시작 (2026-09-12)

새task a1_flat_jump_supported_v4, PrecisionJumpEnv 및 P2-03 엄격 성공 그대로. JumpEnv dense에서landed 이후에만2.0*vz² +1.0*(1-contact_on.float().mean) 비용을차감하고dt곱함. P2-03 등옛config는두가중치default0. 최초착지전추가비용0, 반경/hold/힘threshold/관측66/PPO/구동기변경없음. 결합변경효과만비교하며항별인과주장없음. docs/p2-04-protocol.md 사전고정.

단위28개통과(landing_settle_cost의착지전0/완전지지정지0/속도양음대칭/결손접촉/가중치0 포함). 합성check_precision_jump.py configs/p2-04-supported-jump.json PASS, log artifacts/p2-04-supported-state-check.log. 구현확인64env×2updates 및64개자동평가/영상/진단/hashUUID회수감사PASS: artifacts/p2-04-supported-implementation-check, __final-evaluation. 짧은정책유효비행0으로누락firsttouch값일치만확인,본평가양성일치추가검증필요.

본4run artifacts/p2-04-supported-seed{0,1,2,3} 시작,GPU index=seed,각1024×24×1600updates=39,321,600step. 총157,286,400신규. commit b05f157 실행. supervisor1800초/자동최종64평가영상진단180초. shell session52902/41050/25327/15989. 새턴은실제PID/메트릭관측으로진행하고같은run중복시작금지.

완료후8run audit_artifacts.py감사, experiment_report.py와jump_trace_report.py configs/reports/p2-04.json. A는P2-03재사용4seed,B는P2-04새4seed;이번엔성공계약동일. 온라인firsttouch↔원본200Hz1e-5일치,첫착지와지지유지/수직진동을함께검사. 최종T1J-v4 MP4는result수집. P2-03대조군에P2-04태그override추가했고원본config불변. 자동승격없음. 정밀도약이여러seed에서검증되면다음은수평목표와제한착지면으로진행하며평지보상수정만반복하는것을최종목표로삼지않는다. goal active 유지.

### P2-04 학습 중 모니터링 개선

실제PID703256/703354/703436/703545가살아있고update301–310까지증가했다. 아직새성공0,고정설정유지. evaluator에first_touch_precise_episodes/stabilized_episodes/success_contract 요약만추가(행동·판정불변). 웹은과거정밀평가의results에서첫접촉/기존안정화/전체성공을별도로집계표시하고episode첫접촉열추가. 기존완주율표기는과제성공률로수정. 사용자지정서버18710기존배포체계유지,TS/Vite build통과, / 및기존P2-03평가run API200. 원본artifact변경없음. 새평가는추가요약필드도저장하므로완료후실제출력확인. goal active.

## P2-04 완료: 제자리 정밀 도약과 지지 안정화 재현

4seed1600updates 및각64평가완료. 엄격성공A=P2-03 0/8/0/0 →B=P2-04 전seed64/64. 첫접촉네발반경양쪽전seed64/64유지. B최종height/vz/omega/XY/contact/history위반전부0. 온라인firsttouch-원본오차일치 및8run hashUUID회수감사통과(artifacts/p2-04-audit.jsonl). 최종T1J-v4 영상4개result등록,4GPU회수완료. 자동champion승격없음.

성공B조기종료와실패A4초timeout때문에전체posttouchRMS는같은관측길이가아니다. 추가보조분석first_touch_200ms는첫발접촉부터40표본이며모든A/B64episode window완전. 네발>5N 비율A2.5/36.9/9.8/10.0%→B57.4/77.5/62.5/55.0%. B전발<2N표본0. vzRMS A.281/.360/.552/.542→B.439/.394/.343/.324m/s. seed0/1은증가했으므로모든수직충격감소주장금지. 최종안정화성공개선과초기충격을분리. 결합보상항별인과분리없음.

보고서docs/p2-04-results,summary,height-diagnosis,figures생성. experiment_report.py및jump_trace_report.py configs/reports/p2-04.json재현. evaluator추가요약first_touch_precise_episodes/stabilized_episodes도출력됐다. 동일개발초기조건평지작은높이명령범위로결론제한. 이제평지보상수정을계속늘리지말고수평목표/제한착지면으로진행한다.

### 다음 수평 도약 준비

docs/p2-horizontal-command-design.md 초안과scenarios.directed_jump_scenarios를작성했다. 이함수는아직evaluate.py나env에연결되지않았다. spec evaluation_forward_m=[0,.05,.1,.15],apex_range_m=[.04,.06]를받아같은16높이seed×4거리=64개명령을생성한다. id고유/prefix안정/거리균형/높이pair검증을추가해총30unit PASS. task문자열은아직directed-jump-design이며실제새task/version등록전이다. 기존jump_scenarios변경없음.

목표만옮기면걸어간뒤제자리점프해도성공할수있음. 새P2-05는초기출발영역(제안반경3cm)에서유효비행을확인하고최초비행시점rootXY와최초착지rootXY를기록해실제비행전방이동량을측정해야한다. 비영점목표의최소이동량은제안max(0,목표거리-3cm),0cm명령에는양의이동강제안함. 아직숫자사전고정/물리검증전이므로프로토콜을먼저확정할것. 유효비행감지지연(20mshistory/50Hz판정)으로실제이륙보다늦은시점부터재는보수적거리임을명시. 출발기준은scene.env_origins가아니라calibrated_root[:2]까지반영해야함(기본rootx약-.047m!).

제안구현: DirectedJumpEnv extends PrecisionJumpEnv. reset후4개발goal에동일전방거리(학습0~.15m)를추가,해당거리tensor와launch/landingrootlatch초기화. 첫flight_event에서launchXY저장/출발영역검사. 첫physicsfootcontact(FirstTouch new.any)시rootXY저장;현재precision wrapper확장시기존동작은보존하고새task에만hook을선택적으로호출. 성공은기존엄격성공AND launch영역AND 최소실비행거리. 과거안정화/정밀착지/이동충족을별도기록. 출발영역이탈/지상보행우회/이동없음/반대방향/0cm회귀의합성검증필수. 학습/관측66/물리/구동기/PPO기본유지여부를명시하고새계약체크포인트호환성을분리. 시행전짧은경로검증후4seed고정예산. 현재새학습은없고4GPU사용가능. goal active 유지.

## P2-05 수평 목표 도약 구현 및 본 학습 시작

DirectedJumpEnv extends PrecisionJumpEnv, task a1_directed_jump_v5. train_forward_range_m=[0,.15]를reset마다균등추출해네발목표에동일X추가. set_sequence_offsets가goal_distance도갱신하므로평가manifest적용시명령일치. evaluation_forward_m=[0,.05,.1,.15],같은16높이seed를거리별공유한64개개발명령. 기존66관측목표채널사용,높이4–6cm/구동기/PPO/보상항은P2-04그대로.

FlightTravel 모듈: 첫flight_event에서env-localrootXY를저장하고calibrated_root[:2]반경3cm검사. 영역밖은즉시failure. 첫200Hzfootcontact에서rootXY1회저장,실비행x차이측정. 비영점goal은≥max(0,goal-.03),0goal은양의이동불필요. success=기존정밀hold AND출발/거리. launch조건과순수distance_requirement_met을분리하고travel_requirement_met은결합. 미접촉flight_forward_m=-1/유효성flag별도. phase원본에서launch는처음stage>=1인physics표본의바로이전표본(제어판정직전),invalidlaunch즉시종료는마지막유효표본으로대조한다. 최초touchroot는firsttouch시간의physics표본. reportassert1e-5m. 실제이륙보다늦게감지하는보수적비행거리라는한계명시.

32unit PASS. check_directed_jump.py 합성실험PASS(관측/명령/정지거부/영역밖실제상승비행거부/0cm와15cm합성착지결합성공). artifacts/p2-05-directed-state-check.log. 2update64env train+자동평가와최신출발/거리분리코드추가평가p2-05-directed-validation-v2,총3run감사PASS(artifacts/p2-05-implementation-audit.jsonl). 모두implementation-check태그/본예산제외. 짧은정책유효비행0이므로양성원본root대조는본평가후추가확인필요. 합성teleport는정책성능아님.

본4run artifacts/p2-05-directed-seed{0,1,2,3} 시작,GPU index=seed. 각1024×24×1600updates=39,321,600step,총157,286,400신규. sourcecommit88bf232,supervisor1800초,자동64평가/MP4/200Hz180초. session34664/99649/96009/65827. 새턴에서실제PID/메트릭확인후관측,중복실행금지.

완료후8run감사,experiment_report.py및jump_trace_report.py configs/reports/p2-05.json. 보고서는거리별성공/출발/순수실이동/첫접촉/안정화 및원본firsttouch/root좌표대조. helper에서by_distance를보고하고success_label수평도약성공. 네거리각16개이며기존64개제자리프로토콜과동일평가라고비교하지말것. taskclass는평지뿐이라갭/발판성능아님. 영상T1J-v5별도result등록. 모델승격없고goal active 유지.


## P2-05 완료 및 P2-06 착수 · 2026-09-12

P2-05 네 seed 모두 성공0/64. 유효 비행은 seed1만64/64이고 첫 접촉 정밀1/64, 안정화0/64다. 나머지는 유효 비행0/64. 모두 timeout이며 출발 영역 위반 종료가 아니다. 보고서·원본200Hz 좌표 대조 및8개 run audit 완료. 평가영상4개 result/보존, GPU 회수 확인. [전체 결과](p2-05-results.md).

P2-06은 같은 보상·계약에서 학습 목표를 제자리 또는0–5cm로 제한하는 두 조건×두 seed 비교다. 총157,286,400 신규step,1600updates/run. 사전 프로토콜과 source commit c3f094b를 고정하고 GPU0/1 zero, GPU2/3 short로 시작했다. 현재 상태와 후속 절차는 [active-research.md](active-research.md). 새로운 성능 달성이나 champion 승격을 주장하지 않는다.


## P2-06 완료 / P2-07 착수 · 2026-09-12

P2-06 제자리/0–5cm×두 seed 모두 비행0/64·성공0/64. 8개 실행 감사 및 영상4개 보존, GPU 회수 완료. 원본 상승1.26–2.46cm. [결과](p2-06-results.md). P2-07은 동일 설정의 출발 반경만6cm로 변경한 진단이다. 기존3cm 성공과 직접 동등 비교하지 않고3cm 내 launch 부분집합도 별도 집계한다. source1cb2cf0,4개×1600updates 시작. 현재 절차는 [인계](active-research.md).
