# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 완료된 기준선과 GPU 비교

학습4×1600 및 고정평가4 종료. 성공 seed0/1/2/3:48/64·17/64·51/64·51/64. 15cm0/3/12/16,5cm16/0/16/3 성공(각16회). seed0의15cm는비행거리미달,seed1의5cm는안정화,seed3의5cm는첫접촉정밀도실패. docs/p2-11-results.md 및 summary.json. source96d059f 학습.801/1201반경4.5/3cm reset기록네seed확인. 학습4+기본평가4+추가영상평가1 artifact감사통과,원본200Hz좌표대조통과.

64개 근접구도영상은 p2-11-curriculum-seed3__overview64-evaluation에완료, result에보존. --video-envs64 --video-camera-side4 사용,카메라거리16개와동일.첫프레임시각확인:중앙로봇식별가능,외곽일부잘림. 렌더링활성64개이지모두화면안에있다는뜻아님. 원래평가와거리별성공동일. 네기본영상포함5개보존. 사용자는64개전체를담으려고너무멀리찍지말라고지시했다.

## 현재 실행 / 다음 작업

P2-13 학습4×200 및평가4완료. 모두성공0/64. docs/p2-13-results.md/summary.json. 학습4+평가4감사통과·원본진단대조통과·영상4개보존. num_mini_batches32로기존6144표본/32000gradient갱신을맞췄으나회복미확인. 8192를현재연구기본값으로채택하지않는다. source481b041.

P2-14 실제 지지면 전이 파일럿을 시작했다. docs/p2-14-protocol.md에 4개 고정 checkpoint × 평지/연속/분리 지지면 × 64개 episode 평가를 사전 정의했다. src/parkour/support_geometry.py는 발별 9×12cm 발판, 목표 전이 15cm, 실제 갭 6cm 및 z=-0.5m 포획 평면의 manifest를 생성한다. tests/test_support_geometry.py 2개 통과: 빈 공간과 발판 겹침 검증. artifacts/p2-14-geometry-design에는 기존 calibration XY를 사용한 설계만 저장했다. body 이름은 임시 index이며 실제 asset 순서와 연결해야 한다.

아직 시뮬레이터 연결·물리 probe·정책 평가를 수행하지 않았다. 다음은 평지 calibration 상태 보존과 collider 교체/초기화 경로 조사, 실제 foot collider 크기 확인, 지지면/갭 낙하 probe 실행이다. geometry bounds 테스트를 실제 빈 공간 검증으로 간주하지 않는다. 원래 checkpoint restore 계약을 유지하며 지형 override를 별도 기록한다. 현재 GPU 4개 유휴, 저장소 538GB 여유를 확인했다. 이번 턴은 프로토콜·geometry 구현·테스트·설계 manifest 생성으로 progress다.

P2-11 성공48/17/51/51, P2-12·13모두0. 병렬규모최적화만무한반복하지말고실제불연속지형이라는원래범위진행. GPU프로파일원본및결과docs/gpu-env-sweep-results.md/summary.json.공통동시구간실측/CPU병목분석은미완료. GPU완전활용주장금지.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다. user요청중단전goal active유지.


### 최신 진행: P2-14 독립 물리 probe 완료

scripts/support_probe.py와 run_job의 support_probe kind를 추가했다. `artifacts/p2-14-support-probe-a1-v4`가 최종 유효 probe: 24/24 낙하 위치 검증, A1 발 collider 반지름 2cm·world scale 1 확인, artifact 감사 통과, 실제 worker 종료 및 GPU 회수 완료. USD contact/rest offset null은 zero가 아니라 미명시다. 상세 실패 시도와 범위는 p2-14-protocol 마지막 절에 기록했다. 모든 probe 종료 상태이며 현재 긴 학습 없음.

다음 작업은 robot 평가 장면 연결이다. 기존 SequentialEnv calibration을 보존하면서 plane을 catch floor로 대체하고 유효한 tensor view/reset을 유지하는 방법을 구현·검증해야 한다. 독립 probe 통과를 해당 장면 검증으로 확대 해석하지 않는다. 그 후 사전 정의한 네 seed/세 지형 평가와 64개 근접구도 최종 영상을 생성한다. 이번 턴은 실제 물리 증거를 얻은 progress다.


### 최신: 로봇 발판 환경 연결

make_env(config, evaluation_support=None), FootholdCfg.evaluation_support 및 evaluate의 --support-mode/--support-calibration을 추가했다. frozen calibration은 p2-11 seed0 최종평가 run.json을 공통 사용하고 foot order를 실제 asset에 대조한다. 목표는 모든 episode +15cm로 평가 override한다. 학습 config/restore 계약은 그대로다. collect_results는 조건별 제목과 terrain.json hash/copy를 지원한다.

중요: parent ground transform 이동만으로는 plane collider가 내려가지 않았다. robot-gap-v1에서 검출해 정책 평가 시작 전에 수정했다. 이제 physics 시작 전 Ground prim 전체를 제거하고 -.5m에 새로 생성한다. split-stance-v2 네 대 모두4초 지지, robot-gap-v2 네 대 모두0.08초 실패 및무접촉 관측, 두 artifact 감사통과. 연속 지지면 중앙 검사 robot-bridge-v2 실행 세션74644의 실제 상태를 확인할 것. 현재 정책 비교12개는 아직 시작하지 않았다.

다음은 bridge-v2 정상지지 확인 후 source commit을 기준으로 기존P2-11 seed0–3 × flat/continuous/split ×64episodes 정책 평가, diagnostics200Hz 및 --video-envs64 --video-camera-side4 영상. 실제 발판 첫접촉 위치/내부영역 분석은 추가해야 하며 기존 success만으로 안전한 표면접촉을 단정하지 않는다. 필요하면 낮은높이 포획면과 낙하 종료조건을 별도 probe로 검증한다. 이번 턴은 로봇 장면의 숨은 평면 문제를 발견·수정한 progress다.

추가 확인: robot-bridge-v2도 네 대 모두4초 지지, 무접촉0초, 실패0으로 통과했고 artifact 감사·worker 종료·GPU 회수를 확인했다. 현재 모든 probe 종료, 정책평가 미시작.


### 최신 완료: P2-14 고정 정책 12개 평가

source fe20ba9, batch scripts/p2_14_evaluate.py 세션21428 정상 종료. 4seed×flat/continuous/split×64episode 모두 종료, 12 artifact 감사통과, result 영상12 및 terrain manifest 확인. GPU4개 모두 해제됨. docs/p2-14-results.md/summary.json 및 p2-14-findings.md 참조. 추가학습0step. 평지성공1/5/36/64, 연속·분리 모두0/64 및유효비행0. 원본200Hz 최초접촉오차대조통과.

seed3 episode0에서 .35초 전발무접촉 준비동작 후 .45초 평지는 FR/RL이 초기 발판 바깥에서 재지지하지만 유한지지면에서는 떨어진다. 연속지지면도 실패하므로 갭폭만의 효과가 아니다. 다음은 넓은 단일발판에서 기존정책 진단 후 P2-15 유한지지면 커리큘럼 학습 조건을 고정. 현재 support_geometry는 연속/분리 발별패드뿐이며 넓은 단일발판 mode는 아직없다. 학습중 evaluation_support를 암묵적으로 사용하지말고 새terrain/observation/checkpoint 계약을 설계할 것. 이번 턴은 실제12평가와분석 완료로 progress다.


### 최신 완료: 넓은 단일 발판 추가진단

support_geometry/evaluate/collector에 deck(1.4×1.2m) 추가, tests3통과. source9b4431a, batch --modes deck 세션39295 정상 종료. p2-14-deck-seed0–3 모두종료/감사통과/result4영상확인. 성공31/17/10/21, 유효비행64/25/34/21. scripts/support_transfer_report.py --include-deck로 docs/p2-14-results-with-deck.md 및 summary-with-deck.json 생성, 원래보고서보존.

다음중요: 넓은발판도평지와큰차이가있어 바로학습전에physics contract확인. task.py에서support CuboidCfg에 physics_material을지정하지않았다. TerrainImporter 기본은static/dynamic0.5/rest0이며Cuboid는bindingNone(실제값차이확정아님). 양쪽동일재질명시, USD바인딩/shape/offset계보확인하고새조건평가를원래결과와분리할것. 전체16평가terminal, 현재GPU작업없음. 작은발판에서준비재접촉의존은확인했지만폭만의인과효과라고단정하지않는다. P2-15학습아직미시작. 이번턴4평가완료로progress.


### 최신: 재질비교16개 완료, 학습연결로 진행

source3161fd6. scripts/p2_14_evaluate.py --modes flat continuous split deck --matched-material batch 세션10160 정상종료. 16개 run terminal 및감사통과; result16영상+collision-contract확인. 성공수모든조건기존동일. docs/p2-14-results-with-deck-material.md, summary-with-deck-material.json, material-comparison.json 참조. support-matched-material은명시적TerrainImporter재질을Cuboid에연결하고USD first/last env/ground material과offset을기록한다. -inf값은nonfinite_usd_value문자열로보존. 초기smoke실패는JSON inf직렬화 문제로기록보존, smoke-v2지지/감사통과.

다음은P2-15 실제유한지지면 학습경로와평지예산대조. 평가전용evaluation_support를암묵적으로학습에사용하지말고 terrain config/version, checkpoint strictresume와warmstart의구분, calibratedinitialstate계보를추가해야한다. 초기단계는넓은단일발판에서시작해출발지지를학습하고좁은지지영역/갭으로이행. 아직P2-15 protocol/config/학습코드없다. 재질확인추가만으로연구를대체하지않을것. 현재4GPU모두작업종료상태. 이번턴은16평가와재질계보확인으로progress.


### 현재 실행: P2-15 fresh 유한지형 학습

source ef14a6e. docs/p2-15-protocol.md, configs/p2-15-flat/deck.json. terrain_contract는학습config/checkpoint에포함되고strictresume비교. cfg.support_contract로학습/평가공유. 기존evaluation_support CLI는명시적override. 학습1024env×24×1600, 두조건각4seed, fresh총8run314572800step. launchradius6→4.5→3cm은P2-11동일,새경계관측없음. 단일발판넓은1.4×1.2m에서배우는기준선이며좁은패드/갭해결주장아님.

smoke:3updates+resume4, 같은발판/교차평지4episode의진단영상과scenario일치,4artifact감사,42unit검사통과. scripts/p2_15_train.py 배치세션99332 실행중. GPU0flatseed0→2, GPU1deckseed0→2, GPU2flatseed1→3, GPU3deckseed1→3. 각run후run_job자동same-terrain평가64및영상64/camera4, 이후batch가교차지형평가(__cross-flat/deck)64를실행. --support-preserve-goals로0/5/10/15cm구성유지. timeout1800train240cross.

재시작하지말고실제PID/metrics확인. 초기실행증거:
[{"run": "artifacts/p2-15-deck-seed0", "status": "RUNNING", "pid": 1110684, "live": true, "iteration": 54}, {"run": "artifacts/p2-15-deck-seed1", "status": "RUNNING", "pid": 1110674, "live": true, "iteration": 54}, {"run": "artifacts/p2-15-flat-seed0", "status": "RUNNING", "pid": 1110691, "live": true, "iteration": 57}, {"run": "artifacts/p2-15-flat-seed1", "status": "RUNNING", "pid": 1110675, "live": true, "iteration": 54}]
현재학습완료아님. 다음은살아있는batch진행감시및최종8학습+16평가분석. 학습terrain.json/collision-contract도audit에추가됨. 모든finalvideo result자동저장. 이번턴은학습경로구현·smoke완료·주요학습실행으로progress.


### 학습 감시 및 보고서 설정

P2-15 batch99332 계속실행. 최신확인: deck0PID1110684/update146, deck1PID1110674/update146, flat0PID1110691/update148, flat1PID1110675/update144. 네PID /proc 생존 및실제metrics증가 확인. 최근update평균약0.75초, 각checkpoint100의hash/size모두검증. 아직wave1학습중, 재시작금지.

configs/reports/p2-15.json에 8학습×2평가지형=16평가 목록 준비. scripts/experiment_report.py의 환경step집계를고유run으로중복제거해 총314572800steps를두번세지않는다. 모든평가완료후 experiment_report.py configs/reports/p2-15.json 및 jump_trace_report.py 같은spec 실행. 대표trace는사전에정한episode3(+15cm). 아직결과보고서생성안함. 이번턴은보고서설정·예산집계수정과checkpoint검증으로progress.


### 最新 상태: 첫 묶음 평가 전환

P2-15 deck seed0/1 학습1600완료, same-terrain평가각0/64, validflight0 및64timeout. 두학습모두801/1201반경전환reset기록검증. deck학습2+flatseed1학습+deck평가2 총5artifact감사통과(artifacts/p2-15-wave1-partial-audit.jsonl). 교차평가/나머지학습계속진행. seed2/3까지고정예산비교완료전조건변경하지않는다. 최신실제프로세스목록:
[{"run": "p2-15-deck-seed0", "status": "SUCCEEDED", "pid": 1110684, "live": false, "iteration": 1600}, {"run": "p2-15-deck-seed0__cross-flat", "status": "SUCCEEDED", "pid": 1148391, "live": false, "iteration": null}, {"run": "p2-15-deck-seed0__final-evaluation", "status": "SUCCEEDED", "pid": 1146810, "live": false, "iteration": null}, {"run": "p2-15-deck-seed1", "status": "SUCCEEDED", "pid": 1110674, "live": false, "iteration": 1600}, {"run": "p2-15-deck-seed1__cross-flat", "status": "SUCCEEDED", "pid": 1148561, "live": false, "iteration": null}, {"run": "p2-15-deck-seed1__final-evaluation", "status": "SUCCEEDED", "pid": 1146969, "live": false, "iteration": null}, {"run": "p2-15-deck-seed2", "status": "RUNNING", "pid": 1150396, "live": true, "iteration": null}, {"run": "p2-15-deck-seed3", "status": "RUNNING", "pid": 1150580, "live": true, "iteration": null}, {"run": "p2-15-flat-seed0", "status": "SUCCEEDED", "pid": 1110691, "live": false, "iteration": 1600}, {"run": "p2-15-flat-seed0__final-evaluation", "status": "RUNNING", "pid": 1150166, "live": true, "iteration": null}, {"run": "p2-15-flat-seed1", "status": "SUCCEEDED", "pid": 1110675, "live": false, "iteration": 1600}, {"run": "p2-15-flat-seed1__final-evaluation", "status": "SUCCEEDED", "pid": 1148787, "live": false, "iteration": null}]


### 최신: 첫묶음12artifact검증 및부분보고서

seed0/1 학습4+평가8 모두완료. artifacts/p2-15-wave1-audit.jsonl 12감사통과. docs/p2-15-wave1-results.md/summary.json/height-diagnosis.json 및figures학습/trace 생성, 명세 artifacts/p2-15-wave1-report.json. 최종보고서가아닌부분결과임. 모든평가성공0. flat학습seed0은flat에서validflight64/64 및deck48/64; flatseed1과deckseed0/1은양쪽validflight0. offline flight_episode_count는진단전발무접촉으로validflight와구분.

두번째묶음현재실행PID: deckseed2 1150396, deckseed3 1150580, flatseed2 1153273, flatseed3 1152558. 실제metrics증가확인. batch99332 유지; 중복실행금지. 최종전체8학습/16평가까지예산고정. 각영상result자동보존. 이번턴은완료12artifact감사와원본200Hz대조/부분보고서생성으로progress.


### 최신: P2-15 전체 완료 및 64개 근접 구도 확인

8개 학습과 16개 주요 평가가 모두 SUCCEEDED이며 실제 worker PID가 종료된 것을 확인했다. artifacts/p2-15-audit.jsonl 24개 감사 통과. configs/reports/p2-15.json으로 전체 results/summary/height-diagnosis와 두 figure를 생성했다. 성공 수(seed 0/1/2/3, 각 64회): flat→flat 0/0/10/17, flat→deck 0/0/11/0, deck→flat 0/0/0/48, deck→deck 0/0/0/48. deck seed3은 0/5/10cm 각16/16, 15cm는 비행 이동거리 부족으로0/16. 전체적인 학습 안정성이나 좁은 발판/갭 해결을 주장할 수 없다.

사용자 최신 선호: 64개를 렌더링하되 16개 때와 같은 카메라 거리를 유지하고 바깥 로봇은 잘려도 된다. 기존 evaluation_video_envs=64, evaluation_camera_side=4 및 cross CLI에 이미 반영됨. deck seed3 최종 MP4 0.7초 프레임을 직접 확인했다. 모든64개가 화면 안에 들어온다는 뜻은 아니다. 주요16영상은 result에 저장되어 있으며 smoke2개도 별도로 존재한다.

다음 연구 작업은 P2-15 유한 지지면의 첫 접촉 위치 검증과 실패 원인 종합, 이후 제한된 다음 학습 프로토콜 선정이다. P2-14 분석기의 지형 경계 검증 로직은 재사용할 수 있으나 +15cm 전용 manifest와 현재 혼합 거리 평가를 혼동하지 말 것. 현재 GPU 연구 worker는 모두 종료했으며 새 학습을 시작하지 않았다. 전체 연구 목표는 미완료다.


### 최신: P2-16 거리 커리큘럼 4seed 실행

직전 턴은 P2-15 전체 감사/보고서 생성과 영상 구도 확인으로 progress. 이번 턴은 유한 지지면 진단, P2-16 구현/검증/주요 학습 실행으로 progress다. P2-15 최초 접촉 진단은 scripts/p2_15_support_report.py 및 docs/p2-15-support-diagnosis.md/json. 모든 기존 성공이 보수적 최초 접촉 구 투영 포함 검사도 통과했다. 접촉 쌍이나 지속 지지의 증명은 아니다.

새 사전 프로토콜 docs/p2-16-protocol.md, config configs/p2-16-deck.json. 같은 넓은 발판/초기 calibration/관측/보상/launch 일정에서 목표 거리만 update1–400 0–5cm,401–800 0–10cm,801–1600 0–15cm로 확장한다. 고정 분포 대조군은 완료된 P2-15 deck 4seed를 재사용하고 동시 무작위 대조로 표현하지 않는다. fresh seed0–3, 각각1024×24×1600, 추가157286400step. 실패 시 예산 임의 연장 금지.

launch_curriculum.distance_for_update와 checkpoint 새 curriculum 계약 추가, train에서 전환 시 reset 및 현재 거리 범위를 metric에 기록한다. schedule 없는 기존 config의 동작/기존 checkpoint 계약은 유지한다. unit45 통과. p2-16-distance-smoke 3update에서5/10/15cm 전환과 reset, checkpoint1에서 resume-smoke update2/3 복구, 최종64개 평가/200Hz/영상/아카이브3artifact 감사 통과(artifacts/p2-16-smoke-audit.jsonl). smoke 성공0은 성능 결과가 아니다.

주요 batch scripts/p2_16_train.py 세션96778, source5bb05c7. 실제 PID 및 metrics 확인:
[{"run": "p2-16-deck-seed0", "status": "RUNNING", "pid": 1208366, "live": true, "iteration": 73, "distance_range": [0.0, 0.05], "steps": 1794048}, {"run": "p2-16-deck-seed1", "status": "RUNNING", "pid": 1208384, "live": true, "iteration": 74, "distance_range": [0.0, 0.05], "steps": 1818624}, {"run": "p2-16-deck-seed2", "status": "RUNNING", "pid": 1208383, "live": true, "iteration": 75, "distance_range": [0.0, 0.05], "steps": 1843200}, {"run": "p2-16-deck-seed3", "status": "RUNNING", "pid": 1208387, "live": true, "iteration": 74, "distance_range": [0.0, 0.05], "steps": 1818624}]

현재 학습 중이며 재시작하지 말 것. 다음은 이 PID와 metrics 증가 감시, 종료 후 학습4+평가4 감사, configs/reports/p2-16.json으로 experiment_report.py와 jump_trace_report.py 실행. 기존 대조4개와 seed별/거리별 비교하고 지지면 진단도 추가한다. 각 final 평가64개 camera-side4, result와 step:p2-16-distance-curriculum 태그 자동 저장. GPU0–3 모두 사용자 자원 사용, 착수 전 유휴 확인, 디스크 여유536GB. 전체 연구 목표 미완료.


### 최신: P2-16 체크포인트 및 모니터링 검증

동일 batch96778의 네 PID 생존과 metrics 증가 확인. checkpoint100 모두 hash 정상, 현재까지 loss 유한. artifacts/p2-16-watch.jsonl에 관측 기록. API의 step:p2-16-distance-curriculum 검색에서 네 RUNNING 작업과 실제 거리 범위 metric 노출 확인. 실제 최근 상태: [{"run": "p2-16-deck-seed0", "pid": 1208366, "live": true, "iteration": 218}, {"run": "p2-16-deck-seed1", "pid": 1208384, "live": true, "iteration": 220}, {"run": "p2-16-deck-seed2", "pid": 1208383, "live": true, "iteration": 220}, {"run": "p2-16-deck-seed3", "pid": 1208387, "live": true, "iteration": 219}]

scripts/p2_15_support_report.py에 선택적 report spec 인자를 추가했다. 기본 P2-15 실행 결과는 기존 MD/JSON과 byte 차이 없이 검증했다. 64개 평가의 거리별16개 구성도 float32 허용오차1e-7로 확인한다. P2-16 전체 완료 후 `python.sh scripts/p2_15_support_report.py configs/reports/p2-16.json`으로 첫 접촉 지지면 진단 생성 가능. 현재 미완료이므로 P2-16 결과 보고서는 아직 생성하지 않았다. 이번 턴은 분석 경로 확장/실제 기존 결과 대조/체크포인트 검증으로 progress. 학습 조건 변경 없음, 기존 batch를 계속 관찰할 것.


### 최신: P2-16 첫 거리 전환 검증

이번 턴은 동일한 네 실제 PID(1208366/1208384/1208383/1208387)를 확인한 verified wait 후, update401 전환 증거를 확보했다. 모든 seed에서 train_forward_range_m=[0,0.1], launch_radius_m=0.06, curriculum_reset_all=true를 검증했다. checkpoint400도 네 hash 일치. 최근 진행420/425/422/426, 모두 실제 PID 생존. artifacts/p2-16-watch.jsonl에 기록. 학습/평가를 재시작하지 않았으며 batch96778 계속 실행 중. 다음 전환 검사는 update801의 거리0–15cm와 launch반경4.5cm, 그 다음1201의3cm다. 아직 최종 성능 결과 없음.


### 최신 확인: P2-16 계속 실행
동일 네 PID를 관찰한 verified wait. checkpoint500 네 hash 통과, 최근100update loss 모두 유한, GPU34°C. 최근 상태 [{"run": "p2-16-deck-seed0", "pid": 1208366, "live": true, "iteration": 642}, {"run": "p2-16-deck-seed1", "pid": 1208384, "live": true, "iteration": 638}, {"run": "p2-16-deck-seed2", "pid": 1208383, "live": true, "iteration": 631}, {"run": "p2-16-deck-seed3", "pid": 1208387, "live": true, "iteration": 671}]
다음은 update801 거리0–15cm/launch4.5cm 전환 확인. batch96778 계속 실행 중이며 중복 실행 금지.


### 최신: P2-16 update801 전환 검증

동일 네 PID를 확인하며 기다린 후 모든 seed의 update801에서 목표거리[0,0.15], launch반경0.045, curriculum_reset_all=true를 검증했다. checkpoint800 hash 네 개도 일치한다. 최근 update seed0/1/2/3=835/814/805/858, 모두 실제 PID 생존. 원시 관측은 artifacts/p2-16-watch.jsonl. batch96778 유지, 다음은1201의3cm 반경 전환과 최종1600 이후 자동평가. 이 턴은 verified wait와 전환 검증이며 최종 성능 결과는 아직 없다.


### 최신: P2-16 checkpoint1000 검증

동일 batch96778 네 PID를 확인한 verified wait. checkpoint1000 네 hash 일치, 최근 관측 update seed0/1/2/3=1036/1002/1007/1053. 실제 PID 모두 생존, 최근100update loss 유한. artifacts/p2-16-watch.jsonl에 관측 보존. 다음은1201의 launch3cm/reset 전환 확인 후1600 최종학습/자동평가 및 전체 보고서 생성. 중복 실행이나 예산 변경 없음.


### 최신: P2-16 마지막 전환 검증

동일 PID를 확인한 verified wait 후 네 seed 모두 update1201에서 launch3cm, 목표거리0–15cm, reset_all=true를 검증했다. checkpoint1200 네 hash도 정상. 최신 상태 [{"run": "p2-16-deck-seed0", "pid": 1208366, "live": true, "iteration": 1282, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-16-deck-seed1", "pid": 1208384, "live": true, "iteration": 1243, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-16-deck-seed2", "pid": 1208383, "live": true, "iteration": 1256, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-16-deck-seed3", "pid": 1208387, "live": true, "iteration": 1319, "transition1201_verified": true, "checkpoint1200_hash_ok": true}]
다음은1600 종료 및 자동평가,8artifact 감사 후 configs/reports/p2-16.json으로 연구/trace/지지면 보고서 생성. batch96778 유지, 중복 실행 금지. 전체 연구 미완료.


### 최신: P2-16 전체 완료 및 실패 해석

학습4개+최종평가4개 SUCCEEDED, 실제 모든worker PID 종료/GPU 유휴 확인. artifacts/p2-16-audit.jsonl 8감사통과. experiment_report/jump_trace_report/p2_15_support_report configs/reports/p2-16.json 모두완료. docs/p2-16-results/summary/height-diagnosis/support-diagnosis 및 figures 생성. result 주요영상4개 hash 대조, seed2 프레임시각검사. 결과32/1/48/5, 유효비행모두64. 기존대조0/0/0/48. 모든15cm실패, seed2 평균비행11.66cm가요구12cm미달. seed1 안정화,seed3 RR첫접촉 오차도실패원인. docs/p2-16-findings.md 해석 참조.

다음 구체 과제: 같은4run checkpoint800/1200를 최종3cm 반경/동일64episode로 평가해 후반퇴화 여부 진단. 아직 시작하지 않았고 별도사전프로토콜 필요. 추가학습step0, 평가8개. configs와checkpoint는원래run계약유지,일반 evaluate restore사용. 태그는 P2-16 내 purpose:checkpoint-diagnosis 추가 또는새 명시적step. 전체연구미완료. 이번턴은verified wait→학습/평가완료감사→보고서/실패해석으로progress.


### 최신: P2-16 중간평가8개 완료

사전 docs/p2-16-checkpoint-protocol.md, script p2_16_checkpoints.py sourcef96c11a/batch90789. checkpoint800/1200×4seed 모두SUCCEEDED 및실제worker종료. artifacts/p2-16-checkpoint-audit.jsonl8감사통과,result8영상hash확인. p2_16_checkpoint_report.py로 docs/p2-16-checkpoint-results.md/summary.json생성. 최종과pairedscenario/원본checkpoint hash/3cm반경동일확인. 추가학습0step.

800→1200→1600 성공수 seed0:32→32→32,1:31→32→1,2:18→0→48,3:24→0→5.15cm모두0. 특정seed퇴화는있으나seed2는후반회복. 단일조기종료해결주장금지. 다음은checkpoint의학습률/정책변화및안정화진단으로다음학습조건선정. 새학습미시작. 이번턴은8평가실행완료/감사/분석으로progress.


### 최신: P2-17 비행 거리 가중치 비교 실행

P2-16 전체64checkpoint 학습률/actor변화/normalizer상태와12평가의최종지지조건진단완료. scripts/p2_16_update_diagnosis.py,docs/p2-16-update-diagnosis.json 및 findings참조. 공통고학습률원인주장근거없음. 다음개입은모든15cm실패에대한기존비행거리보상weight4→12 단일변경. 새단위코드경로없고config차이검증 및45unit통과.

P2-17 사전 docs/p2-17-protocol.md/configs/p2-17-deck.json,source8493c4c. scripts/p2_17_train.py batch77388 실행중. fresh4seed 각1024×24×1600,추가157286400step. 기존 P2-16 동일예산대조재사용. 커리큘럼/관측/행동/나머지보상/성공기준은동일. rawreturn비교로성과판정금지. 최종64개평가+200Hz+근접64영상/result자동저장. 실제초기진행 [{"run": "p2-17-deck-seed0", "pid": 1261669, "live": true, "iteration": 61}, {"run": "p2-17-deck-seed1", "pid": 1261670, "live": true, "iteration": 61}, {"run": "p2-17-deck-seed2", "pid": 1261668, "live": true, "iteration": 63}, {"run": "p2-17-deck-seed3", "pid": 1261648, "live": true, "iteration": 63}]

중복실행금지,같은PID/metrics관찰. 전환401/801/1201 확인 및학습4/평가4종료감사후configs/reports/p2-17.json으로experiment_report/jump_trace_report/p2_15_support_report 실행. 전체연구미완료. 이번턴은진단/단일개입프로토콜/검증/새학습실행으로progress.


### 최신: P2-17 첫 거리 전환

동일 batch77388 네 PID를 확인한 verified wait 및 transition401 검증. 네 seed 모두 거리0–10cm/launch6cm/reset_all=true 확인. checkpoint300 네 hash 정상, 최근loss 유한. artifacts/p2-17-watch.jsonl에 관측보존. 최근상태 [{"run": "p2-17-deck-seed0", "pid": 1261669, "live": true, "iteration": 420, "transition401_verified": true}, {"run": "p2-17-deck-seed1", "pid": 1261670, "live": true, "iteration": 420, "transition401_verified": true}, {"run": "p2-17-deck-seed2", "pid": 1261668, "live": true, "iteration": 422, "transition401_verified": true}, {"run": "p2-17-deck-seed3", "pid": 1261648, "live": true, "iteration": 426, "transition401_verified": true}]
다음은801의0–15cm/4.5cm 전환,1201의3cm 전환 및1600최종평가. 기존실행재시작금지.


### 최신: P2-17 전체 거리 전환 검증

동일PID를확인한verified wait 후 네seed update801 거리0–15cm/launch4.5cm/reset_all=true 확인. checkpoint800 네hash 일치. 최근 [{"run": "p2-17-deck-seed0", "pid": 1261669, "live": true, "iteration": 838, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-17-deck-seed1", "pid": 1261670, "live": true, "iteration": 820, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-17-deck-seed2", "pid": 1261668, "live": true, "iteration": 836, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-17-deck-seed3", "pid": 1261648, "live": true, "iteration": 840, "transition801_verified": true, "checkpoint800_hash_ok": true}]
다음1201의3cm전환,1600종료자동평가. batch77388 유지,재시작금지. 관측 artifacts/p2-17-watch.jsonl.


### 최신: P2-17 마지막 반경 전환

같은 실제PID를 확인한 verified wait 후 update1201의 출발반경3cm/거리0–15cm/reset_all=true를 네seed모두검증. checkpoint1200 네hash정상. 최근 [{"run": "p2-17-deck-seed0", "pid": 1261669, "live": true, "iteration": 1268, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-17-deck-seed1", "pid": 1261670, "live": true, "iteration": 1229, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-17-deck-seed2", "pid": 1261668, "live": true, "iteration": 1269, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-17-deck-seed3", "pid": 1261648, "live": true, "iteration": 1278, "transition1201_verified": true, "checkpoint1200_hash_ok": true}]
다음1600학습종료/자동평가8artifact감사및configs/reports/p2-17.json의3종보고서. batch77388 유지,중복실행금지.


### 최신: P2-17 완료, weight12 채택 기각

학습4+평가4 모두 SUCCEEDED/PID종료. artifacts/p2-17-audit.jsonl8감사통과. configs/reports/p2-17.json으로experiment_report/jump_trace_report/p2_15_support_report 완료,docs결과/summary/height/support+figures생성. result4주요영상hash/seed1프레임시각검사완료. 성공0/0/3/0(기존32/1/48/5).15cm이동충족2/16/16/16으로개선됐으나최초접촉16/15/4/32,안정화0/0/30/0으로손실. weight12단독변경채택기각,성공기준유지.

다음구체방향 docs/p2-17-findings.md: 네발최초접촉모두확인후기록된비행거리와최초접촉오차를결합한보상 검토. 현재 first body touchdown의거리보상과별도발보상이tradeoff를허용할가능성(원인확정아님). 무조건가중치sweep중단. 새프로토콜/보상일회성/미접촉/실패/재접촉테스트및smoke후다음학습. 아직구현/실행안함. 전체연구미완료. 이번턴은wait→학습/평가완료→감사/분석/기각결정으로progress.


### 최신: P2-18 결합 보상 학습 실행

source55a913e, protocol docs/p2-18-protocol.md. TravelLandingReward mode=coupled_first_touch_v1 추가. 네발최초접촉모두seen 때한번 12*exp(-거리오차/.03)*exp(-최대최초발오차/.05),첫bodytouch거리고정,실패사건paid차단,선택reset. 기존distance_only는동작유지. jump엄격checkpoint계약포함. 50unit통과,smoke64env3update+resume4+최종64episode/200Hz/64근접영상/result 및3artifact감사통과. 새보상실제비영지급의단위검사통과; 짧은smoke의성공률을학습성과로주장하지않는다.

주요 scripts/p2_18_train.py batch33864 실행중, configs/p2-18-deck.json. fresh seed0–3,각1024×24×1600,추가157286400step. 대조P2-17 weight12재사용,기존P2-16참고. 모든평가/성공기준/기타조건유지. 관측초기진행 [{"run": "p2-18-deck-seed0", "pid": 1310361, "live": true, "iteration": 55}, {"run": "p2-18-deck-seed1", "pid": 1310352, "live": true, "iteration": 55}, {"run": "p2-18-deck-seed2", "pid": 1310353, "live": true, "iteration": 56}, {"run": "p2-18-deck-seed3", "pid": 1310354, "live": true, "iteration": 56}]

다음같은PID/metrics관찰,401/801/1201전환확인,종료후8artifact감사와 configs/reports/p2-18.json의experiment_report/jump_trace_report/p2_15_support_report실행. batch중복실행금지. 이번턴은보상구조구현/검증/주요학습착수로progress. 전체연구미완료.


### 최신: P2-18 첫 거리 전환 검증

동일 실제PID를확인한verified wait. update401에서네seed모두거리0–10cm/launch6cm/reset_all=true검증. checkpoint300네hash정상,최근loss유한. 현재 [{"run": "p2-18-deck-seed0", "pid": 1310361, "live": true, "iteration": 426, "transition401_verified": true}, {"run": "p2-18-deck-seed1", "pid": 1310352, "live": true, "iteration": 420, "transition401_verified": true}, {"run": "p2-18-deck-seed2", "pid": 1310353, "live": true, "iteration": 419, "transition401_verified": true}, {"run": "p2-18-deck-seed3", "pid": 1310354, "live": true, "iteration": 421, "transition401_verified": true}]
관측artifacts/p2-18-watch.jsonl, batch33864계속실행. 다음801/1201전환과1600최종평가. 중복실행금지.


### 최신: P2-18 전체 거리 전환

동일PID를확인한verified wait 후 update801에서 네seed모두0–15cm/launch4.5cm/reset_all=true검증. checkpoint800네hash정상. 최근 [{"run": "p2-18-deck-seed0", "pid": 1310361, "live": true, "iteration": 859, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-18-deck-seed1", "pid": 1310352, "live": true, "iteration": 824, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-18-deck-seed2", "pid": 1310353, "live": true, "iteration": 838, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-18-deck-seed3", "pid": 1310354, "live": true, "iteration": 825, "transition801_verified": true, "checkpoint800_hash_ok": true}]
관측artifacts/p2-18-watch.jsonl. batch33864유지,다음1201/1600및최종평가. 중복실행금지.


### 최신: P2-18 마지막 반경 전환

동일PID를확인한verified wait 후 update1201의3cm/거리0–15cm/reset_all=true 네seed검증. checkpoint1200네hash정상. 현재 [{"run": "p2-18-deck-seed0", "pid": 1310361, "live": true, "iteration": 1348, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-18-deck-seed1", "pid": 1310352, "live": true, "iteration": 1247, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-18-deck-seed2", "pid": 1310353, "live": true, "iteration": 1308, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-18-deck-seed3", "pid": 1310354, "live": true, "iteration": 1263, "transition1201_verified": true, "checkpoint1200_hash_ok": true}]
다음1600종료/자동평가8artifact감사 및configs/reports/p2-18.json의3종보고서. batch33864유지,중복실행금지.


### 최신: P2-18 완료 및 탐색/평가 차이 발견

4학습+4평가SUCCEEDED, artifacts/p2-18-audit.jsonl8감사통과. configs/reports/p2-18.json 3종보고서완료 및result4영상hash/seed3프레임확인. 결과0/0/0/33,유효비행0/64/0/64,firstprecision0/49/0/64,stable0/0/0/47.15cm모두0. 결합보상안정적기준선채택보류/기각,전체연구미완료.

중요: P2-18 모든학습metrics에서successes합계0,결정적평가seed3은33성공. 400update구간집계docs/p2-18-training-stages.json. seed0/2유효도약극소수,seed1/3은후반거의모두도약. docs/p2-18-findings.md 해석. 다음구체과제는동일고정개발군의sampled policy와deterministic policy비교진단. checkpoint std와실제PPO act/act_inference경로,RNG계약확인후별도사전프로토콜과평가모드추가. 목표분포도다르므로현재만으로noise원인확정금지. 새학습/진단아직미시작. 이번턴은wait→전체완료감사→분석과후속원인분리로progress.


### 최신: P2-19 행동 샘플링 진단 완료

source26a2520, protocol docs/p2-19-protocol.md, batch28613. evaluate.py --action-mode mean|sampled/--action-seed 추가. sample_action은PPO update_distribution의mean/std+독립torch.Generator noise,전체행매step소비로reset RNG와분리. 기존mean act_inference유지. collector sampled모드/RNG를제목과manifest에기록. 51unit통과.

P2-18 최종4모델 mean1+sampled2RNG(20000/20001) 총12평가SUCCEEDED, artifacts/p2-19-audit.jsonl12감사, result12영상hash와sampled제목검증. mean의모든episode 결과가원래P2-18과정확히일치. sampled모두0/64. seed3 mean33성공/64정밀/47안정화→sampled두반복0성공/26,30정밀/0안정화,비행64유지. seed1정밀49→13,15,안정화는모두0. seed0/2는어느모드든도약0. 학습된std평균0.3767/0.9823/0.4924/0.8721(환경스케일적용전). docs/p2-19-results.md/summary.json 및script p2_19_report.py.

다음은학습에서탐색noise크기/지속을명시적으로제어하는고정예산비교. 현재모델의평가샘플링영향은확인했지만noise감소훈련개선은미검증. 도약탐색실패seed0/2도있으므로처음부터탐색제거하지말것. 학습에서std를바꾸면act/logprob/entropy/update distribution 일관성을유지해야함. 새학습미착수. 이번턴은평가경로구현/검증/12평가완료/원인분리증거로progress. 전체연구미완료.


### 최신: P2-20 제한 Gaussian 탐색 학습 실행

sourcee303428, docs/p2-20-protocol.md/configs/p2-20-deck.json. exploration.py BoundedActorCritic.update_distribution에서raw std를floor.05/cap에clamp;rollout/logprob/entropy/update공유. cap buffer checkpoint저장/복원,exploration설정strictrestore비교. 기존config는ActorCritic유지. train은새rollout시절대update로cap적용,미니배치내일정고정,effective std metric기록. 일정1–800 .35,801–1200 .2,1201–1600 .1. clamp외부gradient0이라는효과포함.

53unit통과,64env3update축소cap일정/체크포인트1→2,3resume/최종64평가·200Hz·근접영상·result 및3artifact감사통과(artifacts/p2-20-smoke-audit.jsonl). 실제std상한기록대조.

주요 scripts/p2_20_train.py batch70012 실행중. fresh4seed각1024×24×1600,추가157286400step. P2-18결합보상/나머지계약유지,대조P2-18재사용. 현재 [{"run": "p2-20-deck-seed0", "pid": 1372183, "live": true, "iteration": 73, "std_cap": 0.35}, {"run": "p2-20-deck-seed1", "pid": 1372176, "live": true, "iteration": 73, "std_cap": 0.35}, {"run": "p2-20-deck-seed2", "pid": 1372162, "live": true, "iteration": 74, "std_cap": 0.35}, {"run": "p2-20-deck-seed3", "pid": 1372175, "live": true, "iteration": 74, "std_cap": 0.35}]

다음동일PID관찰,401거리/801거리+cap.2/1201반경+cap.1확인 및훈련중successes유무검사. 종료후8artifact감사와configs/reports/p2-20.json으로3종보고서. sampled후속평가에서effective std는raw model std가아닌복원된clamp분포를사용할것. 이전p2_19_report.py의raw std표를이모델에그대로적용금지. 전체연구미완료. 이번턴구현/검증/새학습시작으로progress.


### 최신: P2-20 첫 거리 전환 검증

동일실제PID를확인한verified wait. update401거리0–10cm/launch6cm/reset_all=true/std_cap.35 네seed검증. checkpoint300네hash정상,모든기록std상한준수. 최신 [{"run": "p2-20-deck-seed0", "pid": 1372183, "live": true, "iteration": 434, "transition401_verified": true, "training_successes": 0}, {"run": "p2-20-deck-seed1", "pid": 1372176, "live": true, "iteration": 434, "transition401_verified": true, "training_successes": 0}, {"run": "p2-20-deck-seed2", "pid": 1372162, "live": true, "iteration": 434, "transition401_verified": true, "training_successes": 0}, {"run": "p2-20-deck-seed3", "pid": 1372175, "live": true, "iteration": 433, "transition401_verified": true, "training_successes": 0}]
다음801의거리0–15cm/launch4.5cm/cap.2 전환,1201cap.1 및3cm. batch70012유지,중복실행금지. 관측artifacts/p2-20-watch.jsonl.


### 최신: P2-20 cap0.20 전환 검증

동일PID를 확인한 verified wait 후 update801의std_cap.2 및실제std_max<=.2000001,거리0–15cm/launch4.5cm/reset_all=true 네seed검증. checkpoint800네hash정상. 최신 [{"run": "p2-20-deck-seed0", "pid": 1372183, "live": true, "iteration": 842, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 541}, {"run": "p2-20-deck-seed1", "pid": 1372176, "live": true, "iteration": 840, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 223}, {"run": "p2-20-deck-seed2", "pid": 1372162, "live": true, "iteration": 846, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 0}, {"run": "p2-20-deck-seed3", "pid": 1372175, "live": true, "iteration": 837, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 26}]
다음1201의cap.1/3cm전환과최종평가. batch70012유지,중복실행금지.


### 최신: P2-20 마지막 탐색 상한 전환 검증

직전 카메라 설정 확인 턴은 연구 진행 측면에서는 no progress. 이번 턴은 실제 /proc PID가 살아 있음을 확인하고 동일 작업을 기다린 verified wait 후 검증을 수행했다. 네 seed의 checkpoint1000/1200 hash, 전체 기록의 loss 유한성과 실제 std 상한 준수를 확인했다. update1201에서 cap0.1, launch3cm, 거리0–15cm, reset_all=true를 모두 검증했다. 최신 상태: [{"run": "p2-20-deck-seed0", "pid": 1372183, "live": true, "iteration": 1269, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 74356}, {"run": "p2-20-deck-seed1", "pid": 1372176, "live": true, "iteration": 1271, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 20373}, {"run": "p2-20-deck-seed2", "pid": 1372162, "live": true, "iteration": 1293, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 11986}, {"run": "p2-20-deck-seed3", "pid": 1372175, "live": true, "iteration": 1270, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 15393}]

학습 성공이 네 seed 모두 발생했지만 고정 평가군 성능은 아직 미검증. 기존 batch70012를 유지하며 최종1600/자동64개 평가·영상 완료 후 8 artifact 감사 및 configs/reports/p2-20.json의 세 보고서를 실행한다. GPU 약3GB/34–35도, 저장소535GB 여유. 중복 실행 금지. 전체 연구 목표는 미완료.


### 최신: P2-20 완료 및 거리 부족 진단

직전 턴은 실제 PID 확인 후 전환/체크포인트 검증으로 progress. 이번 턴은 동일 학습 PID를 기다려 1600 완료, 자동 평가 PID 1396619/1396612/1396223/1396823의 실행과 종료를 확인했다. 학습4+평가4 SUCCEEDED, artifacts/p2-20-audit.jsonl 8감사 통과. configs/reports/p2-20.json의 experiment_report/jump_trace_report/p2_15_support_report 완료. 새 scripts/p2_20_training_report.py로 완료1600개 metric·고정예산·finite loss·전체 std 상한을 검증하고 단계별 통계 생성. result4영상 hash/camera4/64개 및 seed0 0.8초 프레임 확인.

최종 성공48/48/24/22, 유효비행64/64/64/64, 최초정밀64/64/64/64, 안정화64/64/40/45. 대조P2-18 성공0/0/0/33. seed3은 감소. 15cm는 전seed0/16이며 최초정밀/안정화는 모두16/16, 비행거리만 미달. 실제 평균11.26/8.13/9.47/6.12cm, 최소기준12cm. docs/p2-20-findings.md 판단 기록. 제한탐색은 후속 기준 후보, champion 승격/전체 연구 완료 아님.

다음 구체 과제: P2-20 checkpoint800/1200 ×4 고정개발군 평가로 거리 능력 미획득/후반상실 분리. 새 사후 진단 프로토콜 작성 후 bounded checkpoint buffer/effective std 복원 확인, 기존 p2_16_checkpoints.py 패턴 재사용. 아직 다음 평가 미실행. raw std를 effective std로 보고하지 말 것. first_travel_reward 최종행0은 step 지급액이라 episode 무지급 근거가 아님.


### 최신: P2-20 중간 진단 완료 및 P2-21 시작

직전 턴은 P2-20 완료/분석으로 progress. 이번 턴은 checkpoint800/1200 ×4 평가 완료, artifacts/p2-20-checkpoint-audit.jsonl 8감사 및 result8영상 hash 확인. source aa67145, batch75118 정상 종료. docs/p2-20-checkpoint-results.md/summary.json. 성공800→1200→1600: seed0 48→48→48, seed1 0→20→48, seed2 16→32→24, seed3 16→0→22. 조사한 세 시점 모두15cm성공0. 모든12 checkpoint의 BoundedActorCritic 실제 복원과 cap .35/.2/.1/effective std 검증 완료.

다음 P2-21 source8236019, configs/p2-21-deck.json, docs/p2-21-protocol.md. P2-20 대비 후반 update801–1600 목표 거리 상한만15→20cm로 확장, 다른 학습/탐색/성공판정은 동일함을 config 비교로 확인. 최종 평가0/5/10/15cm 기존64개 그대로. fresh4seed×1024×24×1600, 추가157286400step. 대조 P2-20 재사용, configs/reports/p2-21.json.

64env3update 축소거리/launch/cap 일정 smoke와 최종평가·영상 완료, 2artifact감사 artifacts/p2-21-smoke-audit.jsonl 통과. 실제20cm/reset/finite loss 및 평가 scenario equality 확인. resume코드는 변경 없으며 이번에 새 resume시험은 하지 않음. 주요 scripts/p2_21_train.py batch59110 실행중, 상태 [{"run": "p2-21-deck-seed0", "pid": 1406069, "live": true, "iteration": 78}, {"run": "p2-21-deck-seed1", "pid": 1406060, "live": true, "iteration": 77}, {"run": "p2-21-deck-seed2", "pid": 1406061, "live": true, "iteration": 80}, {"run": "p2-21-deck-seed3", "pid": 1406043, "live": true, "iteration": 79}]

다음 같은 PID 관찰,401/801의 실제거리20cm/cap.2/reset 및1201cap.1/반경3cm 검증. 1600 종료 후8artifact감사 및 configs/reports/p2-21.json 세보고서/영상hash/거리별분석. 20cm성능 주장 금지(현재 평가0–15cm). 저장535GB여유. 전체 목표 미완료, 중복 실행 금지.


### 최신: P2-21 첫 거리 전환 검증

직전 턴은 P2-20 진단 완료와 P2-21 착수로 progress. 이번 턴은 동일 실제 PID의 생존을 확인하며 기다린 verified wait 후 update401의거리0–10cm/launch6cm/cap.35/reset_all=true를 네 seed 모두 검증했다. checkpoint100/300 네hash 및 전구간 finite loss 확인. 첫100update의 episode/success/failure/validflight/landed/apex 집계가 대응 P2-20과 seed별·update별 모두 일치(artifacts/p2-21-preintervention-check.json). 이는 전체 학습의 bitwise 동일성을 보장하지 않는다. 최신 [{"run": "p2-21-deck-seed0", "pid": 1406069, "live": true, "iteration": 451, "transition401_verified": true}, {"run": "p2-21-deck-seed1", "pid": 1406060, "live": true, "iteration": 447, "transition401_verified": true}, {"run": "p2-21-deck-seed2", "pid": 1406061, "live": true, "iteration": 456, "transition401_verified": true}, {"run": "p2-21-deck-seed3", "pid": 1406043, "live": true, "iteration": 449, "transition401_verified": true}]

다음801의 실제20cm 전환/cap.2,1201반경3cm/cap.1 검증 후 최종평가. batch59110 유지, 중복 실행 금지. GPU 약3GB/32–33도, 저장535GB여유. 관측 artifacts/p2-21-watch.jsonl. 전체 연구 미완료.


### 최신: P2-21 거리20cm 전환 검증

직전 턴은401전환 검증으로 progress. 이번 턴은 같은 실제PID를 관찰한 verified wait 후 update801의거리0–20cm/launch4.5cm/cap.2/reset_all=true 및 실제std상한을 네seed에서 확인. checkpoint600/800 hash 정상, 전체loss유한. checkpoint400의 model/normalizer 모든tensor가 대응P2-20과 정확히 일치(artifacts/p2-21-checkpoint-prefix.json). 전체 RNG/optimizer/trajectory 동일성 주장은 아님. 최신 [{"run": "p2-21-deck-seed0", "pid": 1406069, "live": true, "iteration": 865, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 757}, {"run": "p2-21-deck-seed1", "pid": 1406060, "live": true, "iteration": 857, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 209}, {"run": "p2-21-deck-seed2", "pid": 1406061, "live": true, "iteration": 876, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 0}, {"run": "p2-21-deck-seed3", "pid": 1406043, "live": true, "iteration": 861, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 22}]

다음1201의launch3cm/cap.1 전환과1600최종평가. batch59110 유지, 중복 실행 금지. 추가 변형 학습 미시작. 전체 연구 미완료.


### 최신: P2-21 마지막 탐색·반경 전환 검증

직전 턴은801전환 검증으로 progress. 이번 턴은 같은 실제PID를 확인한 verified wait 후 update1201의거리0–20cm/launch3cm/cap.1/reset_all=true를 네seed 모두 검증. checkpoint1000/1200 hash 정상, 전체loss유한/std상한 준수. 추가로 변경직전 checkpoint800의 model/normalizer 모든tensor가 대응P2-20과 일치(artifacts/p2-21-preintervention800.json). 최신 [{"run": "p2-21-deck-seed0", "pid": 1406069, "live": true, "iteration": 1247, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 23289}, {"run": "p2-21-deck-seed1", "pid": 1406060, "live": true, "iteration": 1242, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 5847}, {"run": "p2-21-deck-seed2", "pid": 1406061, "live": true, "iteration": 1267, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 7849}, {"run": "p2-21-deck-seed3", "pid": 1406043, "live": true, "iteration": 1250, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 6335}]

다음1600완료/자동64평가·200Hz·64근접영상 이후8artifact감사 및 configs/reports/p2-21.json의3종보고서, 거리별 성공/회귀와result무결성 확인. batch59110 유지. 전체 연구 미완료.


### 최신: P2-21 완료, 상한 확장 채택 기각

직전 턴은1201전환 검증으로 progress. 이번 턴은 실제 학습PID를 기다려1600완료 및 자동평가PID1421041/1421572/1420488/1421050 실행·종료 확인. 학습4+평가4 SUCCEEDED, artifacts/p2-21-audit.jsonl8감사통과. configs/reports/p2-21.json의experiment_report/jump_trace_report/p2_15_support_report완료, result4영상hash/camera4/64개 및seed0.8초프레임확인.

성공0/12/44/48, 유효비행64/64/64/64, 최초정밀64/64/64/64, 안정화0/18/44/64. P2-20 성공48/48/24/22. 평균35.5→26으로악화하여상한확장채택기각. seed2만15cm8/16성공,해당거리이동충족16/16/평균13.20cm. 다른seed15cm모두0. 성공사례지지면투영모두확인. docs/p2-21-findings.md.

다음 구체 작업: 기존200Hz trace로 최초착지 후 발별목표영역이탈 진단. 안정화실패seed0/1/2 64/46/20개의최종행모두 feet_in_radius=false,contact/support/vz/omega는통과. 최초정밀은모두64라서후속목표유지문제근거. 종료시점만으로원인확정금지. P2-20/21 matched scenarios 비교해이탈시점/오차/지지중발중심이동/최대유지구간분석. 실제미끄러짐판정아님. 추가학습아직미실행,무조건거리sweep금지. 전체목표미완료.


### 최신: P2-21 착지 이후 발 목표 유지 진단 완료

직전 턴은P2-21 완료/분석으로 progress. 이번 턴은 scripts/post_landing_report.py를 작성해 configs/reports/p2-21.json의512episode 원본200Hz기록 분석. docs/p2-21-post-landing.md/json 및figures/p2-21-post-landing.png 생성. 최초접촉KPI1e-5m대조/pairedscenarios/200Hz/validmask, 연속구간공집합·단일·분리·정확200ms synthetic검사 통과. 그림동일scenario0 첫0.6초공통축; 전체진단JSON보존.

안정화실패P2-20 43개 + P2-21 130개=173개 모두 접촉완료후200ms안에영역이탈 관찰, 이후200ms 네발기하유지구간없음. 모두RR이탈. P2-21 실패seed0/1/2 RR최종평균5.80/5.40/5.25cm. 8실행진단발순서FL/FR/RL/RR와동결target/terrain계약일치. 코드robot/contact순서assert/원래jointarray행동연결확인, 순서오류증거없음(동역학대칭성보장아님). 50Hz판정재현/미끄러짐원인확정아님.

다음구체과제: P2-20 기준에서 착지후 dense precision의mean aggregation만worst-foot aggregation으로 바꾼 단일변경 고정예산 비교. 모든발동등,특정RR가중금지. 최초접촉/거리/성공조건유지. 새protocol/설정엄격계약/보상단위검사/짧은smoke후주요학습. 아직구현·학습미착수, 전체목표미완료. 현재실행GPU학습없음.


### 최신: P2-22 착지후 최대오차 보상 학습 시작

직전 턴은512episode 사후진단으로 progress. 이번 턴 sourcea807334, docs/p2-22-protocol.md/configs/p2-22-deck.json. landing_precision.precision_reward는 기존mean을 보존하고 worst_after_landing_v1일 때 landed 이후에만min(exp(-error²/.06²))-1 적용. [-1,0]범위/step_dt/다른보상유지,특정발가중없음. jump설정strictcheckpoint계약포함. 57unit통과,64env3update+최종64평가/영상 및resume3→4..7검증. artifacts/p2-22-smoke-audit.jsonl3감사통과. 검증식이 --iterations4를절대종료로잘못해석해한번실패했으나 실제CLI는추가4update이므로4..7로수정검증; simulator실패아님. 그검증오류뒤주요배치가먼저시작됐으나즉시조사해계약/finite loss/동일scenario를모두확인. 재실행하지않음.

주요 scripts/p2_22_train.py batch99704 실행중. fresh4seed×1024×24×1600, 추가157286400step,대조P2-20재사용. P2-20과태그/landing_precision_mode외config정확히일치확인. 최신 [{"run": "p2-22-deck-seed0", "pid": 1434460, "live": true, "iteration": 96}, {"run": "p2-22-deck-seed1", "pid": 1434453, "live": true, "iteration": 97}, {"run": "p2-22-deck-seed2", "pid": 1434435, "live": true, "iteration": 99}, {"run": "p2-22-deck-seed3", "pid": 1434445, "live": true, "iteration": 98}]

다음 같은PID관찰,401/801/1201커리큘럼/체크포인트검증,최종1600/자동평가후8artifact감사와 configs/reports/p2-22.json의 experiment_report/jump_trace_report/p2_15_support_report/post_landing_report. 도약/최초정밀/안정화/거리/성공 및착지회피함께검토. result64근접영상/태그자동. 전체목표미완료, 중복실행금지.


### 최신: P2-22 첫 거리 전환 확인

직전 턴은 보상구현/검증/학습착수로 progress. 이번 턴은 동일실제PID를 확인하며 기다린 verified wait 후 update401 거리0–10cm/launch6cm/cap.35/reset_all=true 및모든loss유한/std상한검증. checkpoint100/400 hash정상. 최신 [{"run": "p2-22-deck-seed0", "pid": 1434460, "live": true, "iteration": 445, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-22-deck-seed1", "pid": 1434453, "live": true, "iteration": 455, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-22-deck-seed2", "pid": 1434435, "live": true, "iteration": 449, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-22-deck-seed3", "pid": 1434445, "live": true, "iteration": 451, "transition401_verified": true, "checkpoint400_hash_ok": true}]

첫400update P2-20/22의episode/flight/landed/success를 artifacts/p2-22-first-stage.json에저장. 초기구간비교만으로최종성능이나착지회피확정금지. GPU약3GB/32–33도, 저장534GB여유. 다음801/1201전환 및1600최종평가. batch99704 유지,중복실행금지. 전체연구미완료.


### 최신: P2-22 전체 거리와 탐색상한 전환 검증

직전 턴은401전환/초기집계로 progress. 이번 턴은 동일실제PID 확인 후 verified wait 및 update801의거리0–15cm/launch4.5cm/cap.2/reset_all=true 검증. checkpoint500/800 hash정상, 전체loss유한/std상한준수. 최신 [{"run": "p2-22-deck-seed0", "pid": 1434460, "live": true, "iteration": 855, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 492}, {"run": "p2-22-deck-seed1", "pid": 1434453, "live": true, "iteration": 892, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 0}, {"run": "p2-22-deck-seed2", "pid": 1434435, "live": true, "iteration": 869, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 26}, {"run": "p2-22-deck-seed3", "pid": 1434445, "live": true, "iteration": 863, "transition801_verified": true, "checkpoint800_hash_ok": true, "training_successes": 2175}]

401–600 구간 seed0/2/3은대부분도약/착지, seed1은24632episode 중validflight286/landed0. 최종판정아니며착지회피가능성을계속검토. 다음1201/1600 및자동평가. post_landing_report는모든발최초접촉이있어야현재실행되므로만약최종모델에미접촉episode가있으면분석에서제외여부/분모를명시하도록수정해야함(성공사례만보고하지말것). batch99704 유지, 중복실행금지. 전체연구미완료.


### 최신: P2-22 마지막 탐색·반경 전환 검증

직전 턴은801전환검증으로 progress. 이번 턴은 동일실제PID 확인 후 verified wait 및 update1201의거리0–15cm/launch3cm/cap.1/reset_all=true 확인. checkpoint1000/1200 hash정상, 전체loss유한/std상한준수. 최신 [{"run": "p2-22-deck-seed0", "pid": 1434460, "live": true, "iteration": 1227, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 37786}, {"run": "p2-22-deck-seed1", "pid": 1434453, "live": true, "iteration": 1291, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 0}, {"run": "p2-22-deck-seed2", "pid": 1434435, "live": true, "iteration": 1264, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 6222}, {"run": "p2-22-deck-seed3", "pid": 1434445, "live": true, "iteration": 1238, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "training_successes": 39659}]

801–1000의seed1은24590episode 중validflight180/landed0/success0. seed0/2/3success10507/46/14326. 실제도약/착지습득실패원인은최종평가와분리진단필요. 다음1600종료/자동64평가·영상,8artifact감사/4보고서(미접촉시post_landing분모명시수정필요). batch99704 유지. 전체연구미완료.


### 최신: P2-22 완료 및 채택 기각

직전 턴은1201검증으로 progress. 이번 턴 동일학습PID와자동평가PID1460458/1458441/1459475/1459979의진행·종료확인, 학습4+평가4 SUCCEEDED. artifacts/p2-22-audit.jsonl8감사통과. configs/reports/p2-22.json의4보고서완료 및result4영상hash/camera4/64개/seed1프레임확인. post_landing_report 미접촉episode별도기록/분모수정,기존512개완전접촉결과정확히유지검증+새seed1미접촉64개실제경로검증.

최종성공0/0/0/8, 유효비행64/0/64/64, 최초정밀64/0/64/64, 안정화0/0/0/8. 기존48/48/24/22보다악화,최악발보상채택기각. docs/p2-22-findings.md. seed0/2/3의미안정화64/64/56 모두200ms내영역이탈/200ms기하유지부재. seed1은도약미습득.

마지막400update훈련success/episode61543/87774,0/49190,44585/74514,47635/78399인데최종mean평가차이큼. 다음 P2-23 진단: P2-20+P2-22최종4seed각각sampledRNG20000/20001 총16평가, 기존mean8재사용. 동일64scenarios/정규화고정/effectiveclampedstd확인/추가학습0. 프로토콜부터작성;아직새평가미실행. 기존p2_19_evaluate.py 패턴활용,rawstd표금지. 보상추가변경전에행동샘플링차이분리. 전체목표미완료.


### 최신: P2-23 제한분포 행동샘플링 진단 완료

직전 턴은P2-22완료/채택기각으로 progress. 이번 턴 sourced4cc233, docs/p2-23-protocol.md, scripts/p2_23_evaluate.py batch85643로P2-20/P2-22×4seed×2sampledRNG=16평가 완료. 추가학습0. artifacts/p2-23-audit.jsonl16감사통과, result16영상hash/sample제목/camera4/64개 및샘플프레임확인. scripts/p2_23_report.py는기존mean8재사용+새16의scenario/checkpoint/설정/mode/RNG와실제복원clampedstd검증. docs/p2-23-results.md/summary.json/findings.md.

P2-20 mean→sampled2: seed0 48→47/48,seed1 48→46/44,seed2 24→44/44,seed3 22→27/32. P2-22 seed0 0→40/38,seed1 0→0/0(유효비행0),seed2 0→39/40,seed3 8→46/36. 일부정책의작은행동잡음에따른안정화의존 확인,훈련평가차이전체원인확정아님. 기존P2-22기각유지.

다음구체학습P2-24 후보: P2-20 기준마지막400update std상한0.1→0.05만변경(하한.05유지). 초기탐색/보상/지형/예산/목표유지. mean/sample차이줄이는지별도고정예산비교. 아직프로토콜/구현/학습미시작. 새config/smoke에서floor=cap검증후fresh4seed×1600,대조P2-20재사용. 전체목표미완료. 현재추가학습실행없음.


### 최신: P2-24 마지막 탐색 상한 축소 학습 시작

직전 턴은P2-23진단완료로progress. 이번 턴 source4bf8d8e, docs/p2-24-protocol.md/configs/p2-24-deck.json. P2-20 대비마지막400update(1201–1600) stdcap .1→.05만변경, floor .05유지. config태그외단일차이검증. floor=cap분포/logprob/entropy/buffer복원/경계검사통과. 64env3update축소cap일정 .35/.2/.05 실제검증과최종64평가·영상완료,2artifact감사 artifacts/p2-24-smoke-audit.jsonl. 기존실행코드는변경없음.

주요 scripts/p2_24_train.py batch79919 실행중, fresh4seed×1024×24×1600=추가157286400step,대조P2-20재사용. 최신 [{"run": "p2-24-deck-seed0", "pid": 1472939, "live": true, "iteration": 83}, {"run": "p2-24-deck-seed1", "pid": 1472947, "live": true, "iteration": 83}, {"run": "p2-24-deck-seed2", "pid": 1472940, "live": true, "iteration": 86}, {"run": "p2-24-deck-seed3", "pid": 1472926, "live": true, "iteration": 85}]

다음401/801/1201전환(마지막cap.05)/checkpoint검증,1600후mean평가8artifact감사 및 configs/reports/p2-24.json 4보고서. 이후 최종4seed의sampledRNG20000/20001 총8평가를추가(프로토콜필수),P2-23의P2-20 sampled재사용하여mean/sample차이비교. helper p2_20_checkpoint_report.restored_distribution은1600cap.1하드코딩이므로P2-24에그대로쓰지말것; config일정의완료update-1에서cap검증하도록일반화하거나별도검증. 아직sampled실행스크립트미작성. 전체목표미완료,중복실행금지.


### 최신: P2-24 후속 샘플링 평가 준비

직전 턴은P2-24착수로progress. 이번 턴 현재실제학습PID확인 후후속 scripts/p2_24_sampled.py / p2_24_sampling_report.py작성. train4+mean4감사가통과해야sampled시작,현재RUNNING상태에서실행을거부하고새worker를생성하지않는것을검증. 본학습중복실행아님.

restored_distribution은checkpoint설정의완료update-1로cap을계산하고floor도설정에서읽음. 기존P2-20 12checkpoint결과정확히동일+P2-24 smoke완료3 cap.05실제복원검증. script문법검사통과. 주요학습코드변경없음. 현재 [{"run": "p2-24-deck-seed0", "pid": 1472939, "live": true, "iteration": 211}, {"run": "p2-24-deck-seed1", "pid": 1472947, "live": true, "iteration": 210}, {"run": "p2-24-deck-seed2", "pid": 1472940, "live": true, "iteration": 215}, {"run": "p2-24-deck-seed3", "pid": 1472926, "live": true, "iteration": 213}]

다음401/801/1201전환확인,1600+mean평가완료후8artifact감사/4보고서. 이어 python3 scripts/p2_24_sampled.py 실행(새8평가이름p2-24-p2-24-seedS-sampled-rngR),감사후Isaac python으로 scripts/p2_24_sampling_report.py. P2-23의P2-20sampled재사용. 후속아직실행안됨(사전실행거부시험만). batch79919유지. 전체목표미완료.


### 최신: P2-24 첫 거리 전환 검증

직전 턴은후속평가스크립트/분포검증일반화로progress. 이번 턴은실제동일PID를확인하며기다린verified wait 후401의거리0–10cm/launch6cm/cap.35/reset_all=true 네seed검증. checkpoint300/400 hash정상,전체loss유한. 최신 [{"run": "p2-24-deck-seed0", "pid": 1472939, "live": true, "iteration": 438, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-24-deck-seed1", "pid": 1472947, "live": true, "iteration": 434, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-24-deck-seed2", "pid": 1472940, "live": true, "iteration": 444, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-24-deck-seed3", "pid": 1472926, "live": true, "iteration": 438, "transition401_verified": true, "checkpoint400_hash_ok": true}]

다음801/1201전환(마지막cap.05) 및1600+mean평가,그후사전준비된sampled8평가. batch79919유지, 중복실행금지. 전체목표미완료.


### 최신: P2-24 전체 거리 전환 확인

직전 턴은401검증으로progress. 이번 턴동일실제PID확인 후verified wait 및801의거리0–15cm/launch4.5cm/cap.2/reset_all=true 네seed검증. checkpoint600/800 hash정상,모든loss유한/std상한준수. 추가로checkpoint400 model/normalizer tensor는대응P2-20과모두동일(artifacts/p2-24-prefix400.json). 최신 [{"run": "p2-24-deck-seed0", "pid": 1472939, "live": true, "iteration": 865, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-24-deck-seed1", "pid": 1472947, "live": true, "iteration": 854, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-24-deck-seed2", "pid": 1472940, "live": true, "iteration": 881, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-24-deck-seed3", "pid": 1472926, "live": true, "iteration": 862, "transition801_verified": true, "checkpoint800_hash_ok": true}]

다음1201의실제cap.05/floor.05/launch3cm 검증 및1600+mean평가. 그후sampled8개와P2-23대조보고서필수. batch79919 유지,중복실행금지. 전체연구미완료.


### 최신: P2-24 마지막 실제std0.05 전환 검증

직전 턴은801검증으로progress. 이번 턴동일실제PID 확인 후verified wait 및1201의거리0–15cm/launch3cm/cap.05/reset_all=true,실제std min/max .05 네seed검증. checkpoint1000/1200 hash정상,모든loss유한. 변경직전1200checkpoint의model/normalizer tensor 대조 결과도저장. 최신 [{"run": "p2-24-deck-seed0", "pid": 1472939, "live": true, "iteration": 1255, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "model_equal": true, "normalizer_equal": true}, {"run": "p2-24-deck-seed1", "pid": 1472947, "live": true, "iteration": 1245, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "model_equal": true, "normalizer_equal": true}, {"run": "p2-24-deck-seed2", "pid": 1472940, "live": true, "iteration": 1293, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "model_equal": true, "normalizer_equal": true}, {"run": "p2-24-deck-seed3", "pid": 1472926, "live": true, "iteration": 1262, "transition1201_verified": true, "checkpoint1200_hash_ok": true, "model_equal": true, "normalizer_equal": true}]

다음1600완료+mean평가 후8감사/4보고서, scripts/p2_24_sampled.py 새8평가와 sampling_report필수. batch79919유지,중복실행금지. 전체연구미완료.


### 최신: P2-24 전체 학습·평가 완료

직전 턴은1201검증으로progress. 이번 턴학습4종료/mean4종료실제PID확인 및8감사 artifacts/p2-24-audit.jsonl통과. scripts/p2_24_sampled.py batch68597로새8평가완료, artifacts/p2-24-sampled-audit.jsonl통과. configs/reports/p2-24.json 4보고서 + p2_24_sampling_report완료, result12영상hash/camera4/64개 및meanseed0프레임확인.

mean성공56/32/48/21,유효비행·최초정밀모두64,안정화64/64/64/53. sampled54/59,31/29,47/44,20/24. 기준P2-20 mean48/48/24/22. mean안정화실패43→11. seed0의15cm8/16성공,다른seed15cm0. seed1은10cm비행거리실패로퇴화. mean/sample gap은native std도.1→.05로다르므로동일잡음강건성주장금지. docs/p2-24-findings.md. 승격안함.

다음P2-25 후보는거리상한20cm+마지막std.05조합(기존P2-20:15/.1,P2-21:20/.1,P2-24:15/.05에남은2×2조건). 새로운보상스윕대신두변경의상호작용검증. 기존결과를본뒤설계한탐색적비교임을명시. P2-24 config에서trainrange와마지막distancecurriculum상한만.2로변경,동일고정64평가/4seed예산. 프로토콜/설정/smoke후학습. 아직미착수,현재추가학습없음. 전체목표미완료.


### 최신: P2-25 조합 조건 학습 시작

직전 턴은P2-24전체완료로progress. 이번 턴 source5a27411, docs/p2-25-protocol.md/configs/p2-25-deck.json. 후반거리상한20cm+마지막std.05,나머지P2-24동일. P2-24대비거리변수만/P2-21대비최종cap만차이임을정확한config대조검증. configs/reports/p2-25.json은P2-20/21/24기존12run+새4run으로탐색적2×2비교.

64env3update축소일정의거리.05/.1/.2,cap.35/.2/.05,reset/finite loss/effectivestd검증 및기존64scenario동일확인. smoke학습/평가·영상완료, artifacts/p2-25-smoke-audit.jsonl2감사통과. 주요 scripts/p2_25_train.py batch98960 실행중, fresh4seed×1024×24×1600 추가157286400step. 최신 [{"run": "p2-25-deck-seed0", "pid": 1495130, "live": true, "iteration": 76}, {"run": "p2-25-deck-seed1", "pid": 1495129, "live": true, "iteration": 76}, {"run": "p2-25-deck-seed2", "pid": 1495128, "live": true, "iteration": 78}, {"run": "p2-25-deck-seed3", "pid": 1495131, "live": true, "iteration": 78}]

다음401/801(20cm)/1201(cap.05)과checkpoint검증,1600+mean평가8artifact감사 및configs/reports/p2-25.json 4종보고서. seed별거리/안정화/회귀와두변수상호작용분석. 새로운작은상한sweep반복금지;조합실패시목표표현/정책계약구조적재검토. 저장533GB여유. 전체목표미완료,중복실행금지.


### 최신: P2-25 첫 거리 전환 검증

직전 턴은조합설정검증/학습착수로progress. 이번 턴동일실제PID확인 후verified wait 및401의거리0–10cm/launch6cm/cap.35/reset_all=true 네seed검증. checkpoint100/300/400 hash정상,모든loss유한. 최신 [{"run": "p2-25-deck-seed0", "pid": 1495130, "live": true, "iteration": 438, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-25-deck-seed1", "pid": 1495129, "live": true, "iteration": 434, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-25-deck-seed2", "pid": 1495128, "live": true, "iteration": 441, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"run": "p2-25-deck-seed3", "pid": 1495131, "live": true, "iteration": 439, "transition401_verified": true, "checkpoint400_hash_ok": true}]

다음801거리20cm/cap.2,1201cap.05/launch3cm,1600최종평가8감사/4보고서. batch98960유지,중복실행금지. 전체목표미완료.


### 최신: P2-25 거리20cm 전환 검증

직전 턴은401검증으로progress. 이번 턴동일실제PID확인 후verified wait 및801의거리0–20cm/launch4.5cm/cap.2/reset_all=true 네seed검증. checkpoint500/800 hash정상,모든loss유한/std상한준수. 최신 [{"run": "p2-25-deck-seed0", "pid": 1495130, "live": true, "iteration": 856, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-25-deck-seed1", "pid": 1495129, "live": true, "iteration": 849, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-25-deck-seed2", "pid": 1495128, "live": true, "iteration": 862, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"run": "p2-25-deck-seed3", "pid": 1495131, "live": true, "iteration": 856, "transition801_verified": true, "checkpoint800_hash_ok": true}]

다음1201의cap.05/launch3cm 및1600최종평가8감사/4보고서. batch98960 유지,중복실행금지. 전체목표미완료.


### 최신: P2-25 마지막 탐색 상한 전환 검증

직전 턴은 영상 설정 확인만으로 no progress로 분류하고, 이번 턴 실제 PID 네 개를 다시 확인한 뒤 verified wait 및 1201 전환을 검증했다. 거리0–20cm/launch3cm/cap.05/reset_all=true, 실제 std min/max .05, 모든 loss 유한, checkpoint1000/1200 hash 정상. 최신 [{"run": "p2-25-deck-seed0", "pid": 1495130, "live": true, "iteration": 1254, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-25-deck-seed1", "pid": 1495129, "live": true, "iteration": 1248, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-25-deck-seed2", "pid": 1495128, "live": true, "iteration": 1267, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"run": "p2-25-deck-seed3", "pid": 1495131, "live": true, "iteration": 1262, "transition1201_verified": true, "checkpoint1200_hash_ok": true}]

변경 직전 checkpoint1200의 model 및 normalizer 모든 tensor가 P2-21의 같은 seed와 정확히 일치했다. artifacts/p2-25-preintervention-comparison.json. GPU 온도34–35C, VRAM약3GB씩, 저장533GB여유. batch98960 및 기존PID 유지. 다음1600완료+mean평가8감사/4보고서, 거리·유지성능 및 탐색적2×2 상호작용 분석. 영상64env/camera_side4 유지. 전체연구 미완료.


### 최신: P2-25 학습 및 최종 평가 완료

직전 턴은1201전환·변경전tensor대조로progress. 이번 턴 기존 실제PID를 확인해 verified wait 후4학습/4mean평가 종료와프로세스소멸확인. artifacts/p2-25-audit.jsonl 8감사통과. configs/reports/p2-25.json 비교/height/support/post-landing 4보고서생성, result4영상hash/camera4/64env/태그 및seed2preview 시각확인. GPU4개해제됨.

성공32/29/64/48, 최초정밀·유효비행64전부,안정화64/44/64/50. 거리별seed0=16/16/0/0,seed1=16/13/0/0,seed2=16/16/16/16,seed3=16/16/16/0. 평균43.25/64이나P224대비seed0−24/seed1−3회귀.2×2차이의차이+24/+33/−4/+1,평균+13.5/64 기술통계이며사후설계/작은seed한계. champion승격안함. docs/p2-25-findings.md.

다음은추가작은상한sweep대신P2-26 동결된현재4정책의지지면전이진단. deck/continuous/split 각각동일15cm목표·64episode·동일물리재질 비교,200Hz 준비동작/유효비행/최초접촉/유지 분석. scripts/p2_14_evaluate.py는이전P211고정구현이므로새프로토콜/배치작성,현재학습terrain과evaluation override호환 및동일calibration 확인이필요. scripts/evaluate.py --support-mode/--support-calibration/--support-matched-material 경로존재. --support-preserve-goals 없이15cm고정 override. 네seed모두평가하며좋은seed만선별금지. 현재미착수,추가학습없음. 전체연구미완료.


### 최신: P2-26 지지면 전이 12평가 완료

직전P225완료턴은progress. 이번턴프로토콜/배치source7b2a51d,seed0 deck선행검증후나머지11평가수행. scripts/p2_26_evaluate.py batches87380/37008/44216모두정상종료. artifacts/p2-26-audit.jsonl12감사통과. scripts/p2_26_report.py 및 p2_26_preparation_report.py 실행완료. result12영상hash/camera4/64env/태그,seed2 split preview 확인.GPU전부회수,저장533GB.

deck성공0/0/64/0,flight전부64. continuous/split모든seed성공0/flight0/비발충돌64. 좁은지지면512episode모두초기발XY내부,후속XY이탈/발높이−2cm아래관측. seed2 FR0.355초이탈/0.425초표면아래,continuous종료.46/split.44. docs/p2-26-findings.md/summary.json/preparation.json. 유효비행전지지손실이며갭만의문제아님. 원인과미끄러짐확정금지.

다음P227은좁은continuous학습분포/준비동작의구조적수정후보. terrain_contract flat/deck전용확장및목표영역가용성(20cm목표를현24cm패드에무조건넣지않음)/reset/restore/물리probe검증필요. 관측경계추가와지형분포변경을동시에섞지말고먼저프로토콜/비교예산고정. 기존deck회귀유지. 현재P227미착수,추가학습없음,전체목표미완료.


### 최신: P2-27 continuous 직접 학습 시작

직전P226전체완료는progress. 이번턴src/parkour/terrain_contract.py에continuous허용/버전geometry일치/발투영반경2cm 및모든train/eval/curriculum목표영역검증추가. 기존flat/deck계약유지. tests58통과 artifacts/p2-27-unit-tests.log. configs/p2-27-continuous.json은P224에서terrain/tags만차이임을정확대조. fresh4seed예산동일,지도관측/보상변경없음. docs/p2-27-protocol.md.

source5f2d3c1 smoke64env3update 거리5/10/15cm·반경6/4.5/3cm·cap.35/.2/.05 확인/유한loss. autoeval+영상완료. zero-support64대모두4초실패0,settle후모든200Hz표본네발>2N 확인. resume3→4/5update유한loss/체크포인트확인. artifacts/p2-27-smoke-audit.jsonl4감사통과. 이것은학습성공증거아님.

sourcebd8bd54 scripts/p2_27_train.py batch39983(출력 artifacts/p2-27-main-batch.log),4실제PID실행확인: seed0 1522303/seed1 1522214/seed2 1522215/seed3 1522200. 각1024×24×1600,신규157286400step. artifacts/p2-27-start-observation.json. 저장532GB. 중복실행금지.

다음401/801/1201실제전환및checkpoint확인후1600+continuous mean평가. 이어새모델4개의deck혼합거리회귀평가와P224모델4개의continuous혼합거리대조평가필수(--support-preserve-goals 사용,같은고정calibration/matched). 기존P224 deck평가4재사용. 총비교16행/새평가12,학습4감사. report spec/추가평가배치는아직작성전. scripts/p2_15_support_report.py는foot='all'기반deck전용surface선택가능성있으므로continuous지원확인후사용. 지지면밖성공을확정성공으로과장금지. P226은15cm고정군이므로혼합거리대조에대신넣지않음. 전체목표미완료.


### 最新: P2-27 교차 평가 준비

직전턴은continuous학습계약/물리smoke/본학습착수로progress. 이번턴configs/reports/p2-27.json 16행과 scripts/p2_27_cross_evaluate.py 8개추가평가작성. 학습중RUNNING이면사전감사에서거절하여실제평가worker를시작하지않음을확인 artifacts/p2-27-cross-preflight.log. 모든학습/기본평가종료후실행해야함.

scripts/p2_15_support_report.py continuous명시지원:발별기대pad의XY경계+2cm여유검사,flat/deck경로유지. 실제continuous smoke원본대조실행,기존P224모든row수치정확일치(정의문구만일반화). scripts/experiment_report.py/jump_trace_report.py/post_landing_report.py는공통spec사용. 보고서smoke증거artifacts/p2-27-smoke-check-support-diagnosis.*.

최신실제프로세스 [{"seed": 0, "pid": 1522303, "live": true, "iteration": 179, "log_mtime": 1789172845.0453389}, {"seed": 1, "pid": 1522214, "live": true, "iteration": 183, "log_mtime": 1789172845.1253374}, {"seed": 2, "pid": 1522215, "live": true, "iteration": null, "log_mtime": 1789172688.9121442}, {"seed": 3, "pid": 1522200, "live": true, "iteration": 183, "log_mtime": 1789172845.3813326}]. seed2 PID1522215는시뮬레이터Starting simulation단계로metrics미생성,약2분20초CPU사용중(14core규모)/GPU약2GB. 아직실제프로세스살아있으므로초기화지연으로기록하고임의중복재시작하지않음. 다른3seed진행중. 다음동일PID/CPU시간/log/metric증가확인,401전환및cp검증. batch39983유지,전체목표미완료.


### 최신: P2-27 세 seed의401전환 및 seed2초기화정체조사

직전턴교차평가준비는progress. 이번턴동일PID확인/verified wait후seed0/1/3의401목표0–10cm/reset_all=true/반경6cm/cap.35,모든loss유한및checkpoint100/200/300/400해시확인. 최신 [{"seed": 0, "pid": 1522303, "iteration": 437, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"seed": 1, "pid": 1522214, "iteration": 447, "transition401_verified": true, "checkpoint400_hash_ok": true}, {"seed": 3, "pid": 1522200, "iteration": 443, "transition401_verified": true, "checkpoint400_hash_ok": true}].

seed2 PID1522215는metrics/checkpoint미생성이고Starting simulation단계로로그정체. 실제CPU작동하며 /proc thread 두표본91초간carb.tasking CPU ticks지속증가를확인: artifacts/p2-27-seed2-threads.json 및 thread-deltas.json. gdb스택조회는ptrace_scope1로거절;sudo -n도password required. 보안설정변경/비밀번호요청/정상worker중단안함. deadlock원인확정금지. 기존run_job1800초timeout계약유지하며실제종료전중복재시작금지. 해당초기화손실은인프라시간으로계상할것.

다음seed2동일PID및지표진입여부/감독자실제상태확인,정상3seed801/1201전환. seed2가실제timeout종료한다면원본FAILED/로그를보존하고GPU해제를검증한뒤학습step0부터같은seed/설정새attempt의제한적재시도검토(성능실패seed교체와구분). 아직재시도없음. batch39983유지,전체목표미완료.


### 최신: P2-27 첫400구간의 기준선 대조

직전턴401전환/정체진단은progress. 이번턴동일실제4PID확인,seed2여전히초기화중(약7분CPU누적증가)/metrics없음. 다른3seed진행중 [{"seed": 0, "pid": 1522303, "iteration": 531}, {"seed": 1, "pid": 1522214, "iteration": 543}, {"seed": 2, "pid": 1522215, "iteration": null}, {"seed": 3, "pid": 1522200, "iteration": 540}].

scripts/p2_27_stage_report.py로완료된update1–400만대조, docs/p2-27-first-stage.md/json생성. 기존P2244seed도초기성공0;새3seed성공0,유효비행/재접촉있으나실패수가많다. episode수다르므로rawcount로개선주장금지. pending seed2를실패0/성공0수치로넣지않고명시적미완료행으로보존. 고정평가와구분.

다음801/1201 및checkpoint검증. seed2는기존1800초감독timeout까지동일PID관측,종료가권위있는상태로확인되면실패원본/lease/GPU해제확인후한번의동일seed새attempt재시도검토. 아직살아있고재시도없음. 전체목표미완료.


### 최신: P2-27 세 seed의801전환 검증

직전턴첫400구간보고서생성은progress. 이번턴실제4PID를확인하고여러차례verified wait후seed0/1/3의801전환검증:거리0–15cm/반경4.5cm/cap.2/reset_all=true. 모든loss유한,checkpoint500/600/700/800해시정상. 최신 [{"seed": 0, "pid": 1522303, "iteration": 836, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"seed": 1, "pid": 1522214, "iteration": 857, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"seed": 3, "pid": 1522200, "iteration": 845, "transition801_verified": true, "checkpoint800_hash_ok": true}, {"seed": 2, "pid": 1522215, "live": true, "iteration": null, "status": "initializing"}].

seed2 PID1522215는여전히Starting simulation/metrics없음,기존1800초감독예산안에서진행중으로추적한다. 무단중복재시도없음. 다음정상3seed1201전환및1600평가,seed2종료또는실제진입확인. 교차평가전체배치는4seed완료조건이라현재실행불가;후속seed2복구attempt를진행하게되면명세/경로/계보를명시갱신할것. 전체목표미완료.


### 최신: P2-27 초기화 정체 자원 계상

직전801검증턴은progress. 이번턴실제4PID재확인후 docs/p2-27-initialization-incident.md 및 artifacts/p2-27-resource-snapshot.json 작성. 약789초 관측시점seed2기록학습step0/할당GPU시간하한.2193h/CPU11840초. 다른세seed918/935/924update. GPU프로세스존재와실제GPU연산시간을구분하고초기화정체의원인을확정하지않았다.

기존1800초감독제한유지,종료후원본실패/로그/자원계상보존+같은seed설정새attempt최대1회검토라는제한적복구절차문서화. 아직재시도없고PID1522215살아있음. 다음1201전환검증및1600평가,seed2동일PID/감독자상태추적. 초기화실패의재시도는0학습step인프라복구이며성능이낮은seed교체와구분. 전체목표미완료.


### 최신: P2-27 세 seed의1201전환 검증

직전정체자원계상턴은progress. 이번턴실제4PID확인/verified wait후seed0/1/3의1201전환검증:거리0–15cm/반경3cm/cap.05/reset_all=true,실제std min/max.05. 모든loss유한,checkpoint900/1000/1100/1200해시정상. 최신 [{"seed": 0, "pid": 1522303, "iteration": 1240, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"seed": 1, "pid": 1522214, "iteration": 1257, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"seed": 3, "pid": 1522200, "iteration": 1240, "transition1201_verified": true, "checkpoint1200_hash_ok": true}, {"seed": 2, "pid": 1522215, "live": true, "iteration": null, "elapsed_s": 1049.9855904579163}].

seed2 PID1522215는여전히초기화정체,기존1800초감독제한유지. 다음3seed1600및자동평가종료감사. seed2가완료안되면전체비교를완료로표현하지않고각완료artifact는분석가능. 교차평가전체배치는현재4seed완료게이트유지. supervisor실제timeout종료후원본/자원해제확인하고동일seed새attempt1회복구검토. 아직재시도없음,전체목표미완료.


### 최신: P2-27 세 seed 학습·교차평가 완료, seed2대기

직전1201검증턴progress. 이번턴seed0/1/3의1600완료+auto평가3종료및실제프로세스소멸,artifacts/p2-27-first-three-audit.jsonl6감사통과. source32d09c7에서cross배치 --seeds 옵션추가(중복검사/각요청seed완료게이트),프로토콜에인프라완료순서평가허용/전체4seed요구유지명시. batch6916으로 --seeds0 1 3 교차평가6완료,artifacts/p2-27-cross-first-three-audit.jsonl6감사통과.

configs/reports/p2-27-partial.json은미완료seed2를명시하고3seed12행만포함,4보고서완료. 기존deck→continuous전부0/유효비행0;신규continuous→continuous및deck모두48/64,0/5/10cm16각성공/15cm0거리미달.유효비행/최초정밀/안정화/최초투영포함64전부. 영상9hash/camera4/64env검증. docs/p2-27-partial-findings.md. 전체4seed결론/승격금지.

마지막seed2 PID1522215 RUNNING실제live,elapsed1582초/metrics없음. 감독1800초까지약218초. 현재정상3GPU해제,seed2 GPU2여전히점유. 다음동일PID/감독batch39983관측→실제timeout종료및GPU/lease해제확인→원본실패보존/동일seed2설정새attempt최대1회. 새attempt경로를fullreport/cross/stage보고서명세에명시연결해야함. 이미완료된3seed교차평가중복실행금지. 아직재시도없음. 전체목표미완료.


### 최신: P2-27 seed2 인프라 복구 후 학습 진입

직전3seed학습/교차평가완료는progress. 이번턴동일PIDverified wait후1800초supervisor timeout확인. 원본FAILED/exit−15/timed_out=true/resource_released=false;workerPID1522215 PPID1 orphan/GPU1971MiB잔존. 원본보존+cmdline/소유권확인후해당PID SIGKILL,/proc소멸/GPU없음/lease획득확인. artifacts/p2-27-seed2-orphan-cleanup.json 및 incident문서.

source3e66b5a scripts/p2_27_retry_seed2.py는기록step0/체크포인트없음/터미널timeout/회수검증후최대1재시도. batch40871 실행, artifacts/p2-27-continuous-seed2-retry1 PID1556210 실제live/update23확인. 원본config정확일치,목표1024×24×1600동일. artifacts/p2-27-seed2-recovery.json 계보. 원본실패를삭제/덮어쓰지않음.

full configs/reports/p2-27.json seed2 run을retry1로명시갱신(infrastructure_attempt원본연결). scripts/p2_27_cross_evaluate.py와stage_report도seed2 retry1경로대조. 완료된0/1/3그대로. 다음seed2새PID401/801/1201/1600,기본평가후cross --seeds2만실행(기존3seed중복금지),전체4보고서및16+원본실패회수감사. original batch39983는실패종료예상(확인필요),새batch40871가현재유효학습. 추가재시도없음.

운영결함:run_job timeout시wrapper종료만확인해worker가남음. 향후소유프로세스회수경로를독립테스트로수정할것. 현재retry는정상학습중이므로재시작하지않음. 전체목표미완료.


### 최신: worker 잔존 종료 처리 수정·회귀검증

직전seed2복구턴progress. 이번턴seed2 retry PID1556210 실제live/237update확인. scripts/process_group.py 및run_job수정:wrapper종료와무관하게해당PGID+session의전체살아있는그룹SIGTERM→10초→SIGKILL→5초검증. resource_released는GPU및CPU그룹잔존모두반영,자동평가와정상반환게이트도반영. 이미실행중인retry supervisor는교체안함.

실제프로세스단위3회귀검증+전체61unit통과. synthetic worker 실제run_job timeout session57819는의도대로exit1/FAILED이며,supervisor SIGTERM/SIGKILL/그룹잔존0/resource_released=true 확인. artifacts/cleanup-timeout-regression.* 및 docs/worker-cleanup-regression.md. GPUcompute없는합성검증이므로Isaac GPU해제시험으로과장금지. 다른세션프로세스보존확인.

다음seed2 retry401/801/1201/1600관측,기본평가/cross --seeds2(다른3seed이미완료),full16행4보고서/전체감사. originalbatch39983터미널상태필요시확인. 새batch40871 계속유지,추가재시도없음. 전체목표미완료.


### 최신: P2-27 seed2 retry 첫401전환 검증

직전worker cleanup수정턴progress. 이번턴실제PID1556210확인/verified wait후401전환(거리0–10cm/반경6cm/cap.35/reset_all=true) 및checkpoint100/200/300/400해시·유한loss검증. 최신427update. scripts/p2_27_stage_report.py재생성하여retry1의첫400구간포함,네학습seed완료구간모두확보. seed2 retry 첫400:98154episodes/성공0/실패73263/유효비행52499/재접촉50359. 고정평가성과로해석금지.

기존batch39983터미널핸들조회,새batch40871/PID1556210는계속실행. 다음801/1201/1600+최종평가/cross --seeds2,full4보고서와전체artifact감사. 원본FAILED/cleanup/recovery계보유지. 전체목표미완료.


### 최신: P2-27 seed2 retry 801전환 검증

직전retry401검증턴progress. 이번턴실제PID1556210반복확인/verified wait후801전환(거리0–15cm/반경4.5cm/cap.2/reset_all=true),모든loss유한/checkpoint500/600/700/800해시검증. 최신 {"run": "p2-27-continuous-seed2-retry1", "pid": 1556210, "iteration": 842, "transition801_verified": true, "checkpoint800_hash_ok": true}. GPU2약3GB/32C,초기화정체재발없이업데이트증가.

다음1201/1600+auto평가, scripts/p2_27_cross_evaluate.py --seeds2만실행,full configs/reports/p2-27.json 4보고서/학습4+평가12감사(기존실패는회수/복구별도계보). 완료된3seed교차평가중복금지. batch40871/PID1556210유지,추가재시도없음,전체목표미완료.


### 최신: P2-27 seed2 retry1201 및모니터링확인

직전801검증턴progress. 이번턴실제PID1556210반복확인/verified wait후1201전환(거리0–15cm/반경3cm/cap.05/reset_all=true/실제std min/max.05),모든loss유한/checkpoint900/1000/1100/1200해시검증. 최신 {"run": "p2-27-continuous-seed2-retry1", "pid": 1556210, "iteration": 1252, "transition1201_verified": true, "checkpoint1200_hash_ok": true}.

http://127.0.0.1:18710/api/health 정상/collector errors없음. step:p2-27-support-training 태그로run18/video11조회(실험9+smoke/zero2). 원본FAILED와retryRUNNING/최신metrics분리확인. artifacts/p2-27-monitor-check.json. 원본supervisor의resource_released=false는역사기록이며실제후속회수는orphan-cleanup계보에있음.

다음1600+auto평가, cross --seeds2만실행,full16행4보고서/전체감사/원본인프라손실별도계상. 다른3seed는이미완료. batch40871유지,추가재시도없음,전체목표미완료.


### 최신: P2-27 네 seed 학습·교차평가 전체 완료

직전retry1201검증턴progress. 이번턴retry1600완료/auto평가종료/PID소멸,2감사통과. batch40871정상종료. cross --seeds2 batch13621 완료. configs/reports/p2-27.json 고유24artifact(기존8+신규16) artifacts/p2-27-complete-audit.jsonl감사통과. 4종보고서/신규영상12hash/camera4/64env/seed2preview확인,모든GPU해제/532GB여유.

최종continuous정책:continuous/deck모두48/48/64/48. 0/5/10cm모든seed16각성공;15cmseed2만16/16,나머지거리조건미달. 유효비행/최초정밀/안정화/최초투영포함모두64. 기존P224deck정책continuous전이0/0/0/0 및flight0. docs/p2-27-findings.md. seed0 deck회귀−8남음,champion승격안함.

신규main/평가/초기실패GPU할당시간약2.0732h,실패supervisor1801.33초+회수확인57.22초별도계상. artifacts/p2-27-resource-accounting.json. 원본FAILED보존,retry1계보유지. 기존partial보고서는중간기록으로보존한다.

다음P228 동결된P2274정책 continuous/split ×동일15cm64episode 전이진단. actual gap6cm,wholebody15cm갭주장금지. training path seed0/1/3 p2-27-continuous-seedS;seed2 p2-27-continuous-seed2-retry1. P226batch/report응용가능하나현재아직P228프로토콜/실행미착수. 새지도관측/보상스윕보다준비동작의실제gap전이실패구간을확인. 전체목표미완료.


### 최신: P2-28 동결정책 gap전이 완료

직전P227전체완료는progress. source6f84a2c P228프로토콜/배치,session2139정상종료. continuous/split4seed×64총8평가,artifacts/p2-28-audit.jsonl통과. scripts/p2_28_report.py 및 p2_28_failure_report.py 생성/실행. 영상8hash/camera4/64env/태그/seed2split preview확인.GPU전부해제/532GB.

continuous와split성공모두0/0/64/0. split유효비행0/64/64/64,seed1/3정밀·안정화64지만비행거리11.09/11.31cm로12cm미달. seed2split평균14.74cm,64성공·최초투영포함64. seed0split유효비행전비발충돌64;continuous64episode모두stage0에서split gap위치발중심>5N지지관측,scenario0 FR.455초. counterfactual기하진단이며단일원인확정금지. docs/p2-28-findings.md. single-seed개발군성공/실제gap6cm,wholebody15cm/연속코스/실기성공주장금지. 승격안함.

다음P229후보:기존P2274정책에서동일15cm목표로continuous추가학습vs split추가학습고정예산비교. split에기존5/10cm목표는부적합하므로연속거리curriculum복사금지. terrain_contract현재flat/deck/continuous만지원;split목표가용성검증과checkpoint fork(정책/normalizer초기화,새설정/RNG/optimizer규약명시)추가필요. 동일조건resume와구분,PPO새on-policy rollout. 최종split15cm/continuous혼합거리회귀평가유지. 아직프로토콜/코드/실행미착수. 먼저범위/비교예산을고정하고smoke/물리검증. 전체목표미완료.


### 최신: P2-29 비교계약·split 목표가용성·지지검증

직전P228완료턴progress. 이번턴sourceed92871 docs/p2-29-protocol.md 및 configs/p2-29-continuous.json/split.json 확정. P2274부모정책×2지형,각1024×24×800 신규157286400step. 목표15cm고정/launch3cm/초기cap.1 마지막400cap.05. policy+critic+normalizer계승/optimizer·RNG새초기화의fork를명시하되아직코드구현전. 두config는terrain/tags외정확일치검증. paired order seed0/2continuous먼저,1/3split먼저. primary각2지형15cm64/회귀continuous혼합거리64평가계획.

terrain_contract.py split지원추가,각uniform목표구간전체가하나의pad안에2cm여유로들어가는지검증. [0,.15]양끝점이각각지지돼도중간gap이있으므로거절. eval5cm/curriculumgap횡단거절/개별eval0,15허용테스트포함62unit통과. 기존continuous테스트유지. artifacts/p2-29-contract-tests.log.

zero split probe session51362정상종료,artifacts/p2-29-zero-split-support 감사통과.64대4초실패0/settle후모든200Hz표본네발>2N. autoresult영상생성. 이것은초기지지검증이며학습성공아님. 현재새학습없음.

다음train --fork-from(또는명시명칭) 구현:동일조건resume와상호배타,부모hash/계보/config허용변경리스트,model/normalizer호환tensor검증,새optimizer/RNG/0iteration규약. restore기존strict검사우회로사용금지. 부모model std_cap버퍼.05를복사한뒤새일정.1이rollout전에적용되는지확인. learning.py save_checkpoint에계보보존규약검토. 평가회귀의명시적거리override(부모학습config변경과구분)구현필요;현재sourceconfigevaluation_forward_m15only이므로 --support-preserve-goals만으로혼합거리회귀는안됨. fork양지형smoke/재개/평가검증후본8학습. 아직본학습미착수,전체목표미완료.


### 최신: P2-29 fork 구현·실제학습/재개 검증

직전split계약/지지probe턴progress. sourceed6c2b7 src/parkour/policy_fork.py+train --fork-from 구현. --resume상호배타,config허용변경검사/전체model·normalizer tensor검사후복사,새optimizer/RNG/0계수,새std_cap.1적용. learning.save_checkpoint optional lineage와resume계보보존. checkpoint000000부터부모hash/step을저장. 기존strictrestore유지. 65unit통과.

continuous/split fork smoke각64env3update+auto평가/영상정상완료(34960/24983),4artifact감사통과. 실제cp0의부모model(std_cap제외)/normalizer전tensor동일/optimizer빈값/counters0,cp3신규4608step/동일계보/cap.1→.05→.05검증. splitresume3→4/5(59852)완료/누적7680step/계보보존/별도감사통과. docs/p2-29-fork-validation.md. 본학습아직없음.

다음평가전용명시거리override구현:config의학습jump계약을restore용으로유지한채scenario생성만[0,.05,.1,.15]로바꾸고manifest/meta에저장. split학습모델의회귀는continuous override에서만허용/목표영역가용성검증. 현재--support-preserve-goals는원래config15only이므로충분하지않음. 그후8run순서균형배치/parentseed0,1,3 p227continuous/seed2retry1,각800update/총157286400step. eval15cm각2지형+continuous혼합거리회귀、fullspec작성. 모든smoke후본학습. 전체목표미완료.


### 최신: P2-29 본학습 시작 및 영상 구도 확인

평가 거리 override 구현 commit46778eb, 66개 테스트 통과. 실제 p2-29-regression-smoke에서 학습 config 15cm 유지/평가 0·5·10·15cm 시나리오 일치 및 감사 통과. 배치/primary·regression manifest commit0a050d4. p2_29_train.py PID1608853 실행 중임을 확인했으며 중복 실행하지 않음. 최초 네 작업 continuous seed0/2, split seed1/3의 실제 train worker 존재 확인. 전체 8개 run의 완료나 성능은 아직 확인하지 않음.

사용자 영상 구도 요청 재확인: 64개 렌더링 환경, camera_side=4로 기존 16개 구도 유지; 외곽 일부가 잘려도 중앙 개체 동작이 보이도록 유지. 두 학습 config 및 교차/회귀 평가 스크립트에 이미 반영됨.

다음: 실행 중 batch 상태 확인, p2_15_support_report.py의 단일 15cm 시나리오 및 split 지원 확장 후 primary/회귀 평가·감사·영상·보고서 완료. 기존 보고서 계산 규약 유지. 전체 연구 목표 미완료.


### 최신: P2-29 보고서 지원 및 실행 확인

이전 구도 확인 턴은 설정/실제 batch 확인 및 인계 갱신으로 progress. 이번에는 p2_15_support_report.py에 spec evaluation_distances_m(기본 기존 혼합거리)와 split landing 지지면 판정을 추가했다. split은 고정 landing 목표와 같은 거리인 경우에만 판정하며 다른 목표는 거절한다. 기존 P227 16행의 모든 rows/정책hash/보정hash 동일, P228 8행 512episode 최초 발 투영 포함 판정과 정확 일치 확인. artifacts/p2-29-support-report-validation.json 및 validation 로그/spec 보존. 기존 보고서를 덮어쓰지 않고 별도 validation prefix 사용.

본 batch PID1608853 live, 첫 네 run metrics iteration345~352까지 관측. GPU0~3 VRAM약3.1GB/온도33~34도, 디스크532GB여유. 아직 본학습 완료/성공률 결론 없음. 다음 동일 batch를 재확인하여 완료 후 p2_29_evaluate.py의 사전 감사 gate를 통과해 교차/회귀 실행. 보고서 4종은 primary/regression 두 spec에 적용. 전체 목표 미완료.


### 최신: P2-29 본학습 초기화 감사

이전 턴은 보고서 구현·기존 실제 평가 대조로 progress. 본 batch PID1608853 live 재확인. scripts/audit_policy_fork.py 추가: locally trusted cp0/부모hash, 정책·critic·normalizer exact tensor 복사(std cap/floor 새설정), optimizer state empty 및 초기 LR, config 허용변경, 계보/초기0계수, 기록된 모든 update의 새step 및 탐색cap 일정을 검사한다. 완료 감사와 구분하는 scope를 출력하며 live metrics의 미완성 마지막 줄은 제외한다. 실제 첫4run 감사 통과, artifacts/p2-29-initial-forks-audit.jsonl/log(session44779 exit0). snapshot update480~489, 401부터cap.05 확인. rng 독립성/최종성능을 이 감사로 증명한다고 주장하지 않는다.

앞턴 보고서 validation 임시산출물4개는 artifacts/p2-29-report-validation-*-support-diagnosis.{json,md}로 이동해 보존. 본 batch는 재실행하지 않는다. 다음 첫native평가/둘째묶음 진행 확인, 둘째묶음에도 초기화 감사 적용 후 최종 artifact 감사 및 p2_29_evaluate.py. 전체 목표 미완료.


### 최신: P2-29 모니터링 실제 데이터 검증

이전 턴 fork 감사 구현/실제4run 검증은 progress. 본batch PID1608853 live, metrics610~624 관측. /api/health ok/errors[], phase/step 필터로4 RUNNING 표시, API metrics는파일대비0~3 update 지연, run detail 부모계보와원본정확일치. artifacts/p2-29-monitor-validation.json 저장.

회귀 smoke는split학습config를보존한continuous평가인데상속태그split로분류됨을발견. configs/research-tags.json run_override로p2-29-regression-smoke의terrain:continuous/purpose:regression-smoke 수정,API필터결과검증. 원본연구artifact변경없음. 본교차평가script는명시적실제terrain태그를넘기므로해당오류없음. 다음첫묶음native평가와둘째묶음진행확인. 전체목표미완료.


### 최신: P2-29 첫 묶음 완료, 둘째 묶음 시작

동일 batch PID1608853을45초간격live재확인하며대기,첫continuous seed0/2 및 split seed1/3 학습800+native평가완료. 각64/64성공기록. 학습4+평가4 artifacts감사통과:artifacts/p2-29-first-batch-audit.jsonl. result영상4hash검증,64render IDs/camera framing_side4검증:artifacts/p2-29-first-batch-videos.json. 아직preview직접시각검수및교차지형/혼합거리회귀미완료.

둘째묶음 continuous seed1/3, split seed0/2 RUNNING을run.json과동일live batch로확인. 본총8run완료아님. 다음둘째초기화audit실행및완료평가,이후p2_29_evaluate.py. 최초결과만으로terrain효과/champion승격/일반성공주장금지.


### 최신: P2-29 둘째 초기화 감사 및 첫 묶음 원시 진단

이전턴은첫묶음실제완료/평가/영상감사로progress. 둘째4run audit_policy_fork 통과(session52569exit0),artifacts/p2-29-second-initial-forks-audit.jsonl/log. seed1split preview.png 직접확인:중앙개체와발판보임/외곽일부crop,기존camera4유지. 둘째metrics188~203진행.

첫묶음중간spec artifacts/p2-29-first-batch-intermediate.json. support보고서가native split metadata에goal_forward_m이없어KeyError 발생(원본실패log보존). 공통layout.target_travel_m사용+optionalgoal일치검사로수정. native첫4run256episode모두최초네발구투영포함/성공64각확인. 기존P2288평가512episode진단전체JSON동일검증으로override형식회귀확인. support retry/session85684정상. post_landing도전부최초접촉/안정화완료확인(session24433의postlandingexit0;앞선support오류는별도명시). docs/p2-29-first-batch-intermediate*중간결과/비교미완료문구보존.

다음동일batch둘째학습과native평가완료확인→8학습/8native감사→p2_29_evaluate.py 교차8+회귀8→full primary/regression 보고서. 전체목표미완료.


### 최신: P2-29 본학습 전체 완료 / 교차·회귀 실행 중

이전턴은둘째fork감사/첫묶음진단수정으로progress. 이번동일batch PID1608853을live재확인후45초단위대기. 최종PID종료+batch로그4seed exit0 확인. 8run각800update·19,660,800step,총신규157,286,400step정확일치. 8native평가모두64/64성공,16artifact감사통과 artifacts/p2-29-training-native-audit.jsonl. 8result영상hash/64env/camera4 검증 artifacts/p2-29-training-native-summary.json. 전체비교/회귀결론은미확정.

이어서 scripts/p2_29_evaluate.py 실행시작:session57789,log artifacts/p2-29-cross-regression-batch.log. seed별continuous학습→split평가→continuous혼합거리회귀→split학습→continuous평가→continuous혼합거리회귀 순. 총16평가. 동일세션/실제PID재확인,중복실행금지. 다음완료후평가16감사,두spec에experiment_report/jump_trace_report/p2_15_support_report/post_landing_report 실행,부모/지형간차이와회귀분석. 전체목표미완료.


### 최신: P2-29 교차·회귀 완료 및 집계 오류 수정

이전턴8학습완료/평가시작은progress. session57789정상종료,PID1645482없음+4seedexit0. 교차8/회귀8감사 artifacts/p2-29-cross-regression-audit.jsonl통과. continuous→split15/64/64/64,split→continuous64각. 회귀continuous추가64/48/48/48,split추가64/49/48/48. 모든5/10/15cm16각,0cm만회귀. docs/p2-29-findings.md.

거리override시evaluation.json by_distance가config15only로누락됨을발견;個episode/scenarioはmixed正しく全体success不変。src/parkour/evaluation_summary.py by_distance(records,scenarios)+load_report追加、ID/距離/重複確認、原本不変/sha系譜を添付。evaluate future生成修正、experiment_report/support報告load_report適用。2tests通過、実16評価で距離別episode/成功合計一致。artifacts/p2-29-derived-distance-summary.json。原本書換なし。

primary24行/regression12行の4種報告生成session83437exit0。GPUcomputeプロセス空/531GB。次:モニタリング過去by_distance補正(APIとUI集計経路確認、原本保存)、16新video hash/camera/tags/preview、0cm回帰とcontinuous0split失敗trace診断、P230能力維持計画。全体目標未完了。


### 최신: P2-29 실패 단계 진단·모니터링 집계 적용

이전턴 전체평가/보고서/집계수정은progress. scripts/p2_29_failure_report.py 실제실행 완료, docs/p2-29-failure-diagnosis.json. 0cm seed2/3 양지형 모두16/16 유효비행감지시launch반경3cm밖(원점/200Hz표본일치검사). continuous1 유효비행없음12/반경밖4,split1 정밀착지후안정화미달15. continuous0split 전이timeout49/FR첫오차5cm초과49/RL10. docs/p2-29-findings.md 갱신.

16교차/회귀result영상hash/camera4/render64/실제terrain태그 확인 artifacts/p2-29-cross-regression-videos.json. 대표추가영상시각검수는남음.

monitor collector/API에evaluation_summary.load_report 적용,scenarios파일수정도색인변경감지. 최초서비스재시작후P205구버전distance_requirement_met누락경고발견,구버전계약원래집계유지로수정. unit3+monitor통합7통과. 재시작session6218exit0,실제8회귀API목록/상세네거리일치+health오류없음 artifacts/p2-29-monitor-summary-validation.json. 원본불변.

다음P230: 15cm전용추가학습 대비0cm/15cm 명시적이산혼합목표(갭중간목표금지)로능력유지 비교설계. split훈련출신checkpoint fork허용경계와RNG/새optimizer규약,각목표의split발판역할(0cm departure/15cm landing) 평가진단지원 검토가필요. 아직프로토콜/코드/학습미착수. 연속도약으로확장하기전반복가능한거리명령제어를고정. 전체목표미완료.


### 최신: P2-30 프로토콜 및 이산 목표 샘플링 구현

이전턴 실패단계진단/모니터링집계수정은progress. docs/p2-30-protocol.md 확정: 부모P229split4개,동일split지형15cm전용vsreset별균등0/15cm혼합,각800×1024×24 신규총157286400step. 부모policy/critic/normalizer계승·새optimizer/LR/RNG. 기본native평가는0/15×32,continuous혼합회귀및split15×64보존평가. 부모split혼합군은새평가필요. 본학습미착수.

src/parkour/jump_sampling.py target_ranges/sample_distances 및 DirectedJumpEnv 리셋연결,terrain_contract이산목표별가용성검사. train_forward_choices_m은range/curriculum과동시지정금지. configs/p2-30-fixed.json/mixed.json 작성,혼합은range키제거/choices[0,.15]. 기존연속rand호출값/RNG소비동일테스트,지정값외출력없음/RNG복구/균등샘플/갭목표·중복·nan거절 포함72tests통과(session47878exit0),artifacts/p2-30-sampling-tests.log. torch는sampler함수내import로CPU관리경로의불필요의존성방지.

다음필수: policy_fork의split부모및choices허용변경규약추가(기존strictresume유지),train목표별reset/관측량계상·metric기록(현재active_distance None만으로는혼합기록불충분),support보고서0cm departure/15cm landing 선택,영상제목의이산목표표기,양조건축소학습/평가/재개검증. 아직본학습시작금지(미검증기능남음). 이후8run밸런스순서배치. 전체목표미완료.


### 최신: P2-30 통합 검증 완료·본학습 시작

이전턴프로토콜/샘플러구현은progress. source4741d06 split부모fork 및choices허용변경,목표별reset draws/pre-action envstep 집계,goal선택지로departure/landing 지지면판정,이산학습거리영상제목지원. 74tests통과(session40356),artifacts/p2-30-integration-unit-tests.log.

fixed/mixed64env3update smoke(session9750/89744)둘다학습·native평가·영상정상종료,4artifact감사통과 artifacts/p2-30-smoke-audit.jsonl. 실제cp0부모복사/새optimizer감사2통과 artifacts/p2-30-smoke-fork-audit.jsonl. 각4608step,혼합0cm2607/15cm2001,resetdraw총수와종료수일치. 초기2회reset배정(128개)은meta별도:fixed128,mixed65/63. 집계는attempt진단이며checkpoint커리큘럼상태가아님. 기록 artifacts/p2-30-smoke-goal-accounting.json. support보고서0/15목표선택경로도정상(3update미수렴성능은주장하지않음).

혼합resume3→4/5(session89693)학습+auto평가정상,계보동일·신규3072/누적7680step,2감사 artifacts/p2-30-smoke-resume-audit.jsonl. 원래동일조건resume규약유지.

source d1fec6a scripts/p2_30_train.py 균형8run배치. 본학습시작session68047,log artifacts/p2-30-main-batch.log. 부모P229splitseedS cp800,각P230fixed/mixedseedS cp800계획. seed0/2fixed먼저,seed1/3mixed먼저. 재시작/중복실행금지,현재실제PID확인필요. 다음본학습초기화/목표별계상확인,평가배치/primary회귀spec작성(프로토콜기준split0/15×32 native,continuous0/5/10/15×16,split15×64각8;부모split0/15×32새평가4필요). 전체목표미완료.


### 최신: P2-30 평가 배치·보고서 명세 및 본학습 초기화 확인

이전턴통합검증/본학습시작은progress. 본batch PID1674488 live,첫fixed0/2 mixed1/3 업데이트188~191관측. actualfork감사4통과 artifacts/p2-30-first-fork-audit.jsonl/log(session68119exit0). 모든관측update 목표별step합24576/resetdraw합종료수일치. 혼합step비율은reset균등과달라별도보고필요.

scripts/p2_30_evaluate.py 작성(아직실행안함):seed별parent split0/15×32새평가→fixed continuous혼합회귀→fixedsplit15→mixedcontinuous혼합회귀→mixedsplit15,총20jobs. native8평가는train자동경로. 실행전각8training/native+parent감사,기존출력거절. configs/reports/p2-30-primary/regression/retention.json각12행(부모4+새8),부모regression/retention기존P229재사용,newstep합8run만. 20command모두spec에연결검사.

평가distance_override split지원추가:expected_goal_surface로각목표2cm여유단일표면가용성검사,0/.15허용/.05/.1거절。기존학습config불변. unit75통과(session24173),artifacts/p2-30-evaluation-unit-tests.log. 실제split override실행은본batch완료후parent평가가첫검증이므로시나리오동일성/거리별분모반드시확인.

다음동일본batch진행확인/둘째초기화감사/전체완료후p2_30_evaluate.py. 본학습완료전중복실행금지. 전체목표미완료.


### 최신: P2-30 모니터링 연결 및 이전 영상 검수

이전턴 평가배치/spec/초기화검증은progress. 본PID1674488 live확인,API첫4run249~253update/goal_environment_steps합24576/phase·step·condition태그정상. health오류없음 artifacts/p2-30-live-monitor-check.json. GPU33~34도/약3.1GB/디스크531GB.

P229남은대표교차/회귀영상검수:continuous0-on-split와split2-regression의preview및ffmpeg0.8초추출프레임직접확인. artifacts/*-review-0p8s.png 보존. 구도/렌더링정상,세부발접촉은trace기준,전체프레임육안검수주장금지. findings갱신. 다음동일P230batch진행확인→첫native/둘째묶음→전체완료후20평가. 전체목표미완료.


### 최신: P2-30 첫 묶음 완료·둘째 묶음 실행 중

이전턴 모니터링/영상검수는progress. 이번 동일PID1674488 live확인후45초단위verified wait,첫fixed0/2 mixed1/3각800학습+native평가완료. artifacts/p2-30-first-batch-audit.jsonl 학습4+평가4감사통과. 거리0/15각32개:fixed0=0/32,fixed2=0/32,mixed1=0/32,mixed3=31/32. 여기서쌍의첫수는0cm성공수/둘째수는15cm성공수이며각분모32. 전체조건효과결론아님.

4영상hash/camera4/64render/혼합이산제목검증 artifacts/p2-30-first-batch-summary.json. 둘째mixed0/2 fixed1/3 RUNNING확인. 다음둘째fork감사와완료native확인→전체감사→scripts/p2_30_evaluate.py20jobs→primary/regression/retention3spec보고서. 부모split혼합평가시실제scenario동일성확인필수. 전체목표미완료.


### 최신: P2-30 둘째 초기화 감사 및 목표별 실제 학습량

이전턴첫묶음완료/평가감사는progress. 본PID1674488 live,둘째mixed0/2 fixed1/3 실제fork감사통과(session67104exit0),artifacts/p2-30-second-fork-audit.jsonl/log. metrics170~194확인.

scripts/goal_exposure_report.py 추가:완료artifact감사후spec의새run만선택,각update 목표별step합과resetdraw합을검증하고초기reset배정/rollout중배정/실제환경step을분리집계. 부모재사용예산제외. 첫묶음실제4run적용 artifacts/p2-30-first-batch-intermediate.json→docs/p2-30-first-batch-intermediate-goal-exposure.json,log artifacts/p2-30-first-batch-exposure.log. mixed1 0cmreset49.805%/step65.143%,mixed3 reset49.915%/step52.002%. 초기폐기reset은별도필드보존. 이는노출량이며단일실패원인이나통계적효과주장아님.

다음동일batch완료후8학습/8native감사 및20평가. 전체결과에는goal_exposure_report.py configs/reports/p2-30-primary.json도실행. 현재전체예산추가/조건변경없음. 전체목표미완료.


### 최신: P2-30 전체 본학습 완료 / 추가20평가 실행 중

이전턴 둘째fork/노출량감사는progress. 이번동일PID1674488 live재확인후45초단위verifiedwait,session68047exit0/PID종료/4seedexit0로그확인. 학습8+native8감사통과 artifacts/p2-30-training-native-audit.jsonl. 각800update/총신규157286400step goal_exposure_report로검증 docs/p2-30-primary-goal-exposure.json.

Native split0/15각32개성공:fixedseed0~3 0/32모두, mixed0=29/32,mixed1=0/32,mixed2=0/32,mixed3=31/32. 각쌍첫값0cm성공수/둘째값15cm성공수이며분모각32. 두seed회복만으로일반개선/승격주장금지.

추가20평가 scripts/p2_30_evaluate.py 시작session31532,log artifacts/p2-30-evaluation-batch.log. 부모split0/15×32새4평가부터시작,이어서모델8continuous회귀및split15유지. 다음동일세션/PID재확인·완료후20감사,부모/자식scenario동일성,3spec×4보고서,모든신규result영상hash/camera/tags/대표시각검수,노출량·실패단계최종분석. 전체목표미완료.


### 최신: P2-30 추가평가·보고서 완료

이전턴전체학습/평가시작은progress. session31532exit0/PID1709014없음. 추가20평가감사통과 artifacts/p2-30-additional-evaluation-audit.jsonl. 부모split0cm32/2/0/0,15cm32각. mixed0cm29/0/0/31,fixed0모두0;retention15×64모든12모델행64. continuous회귀mixed:seed0[11,8,16,16],1[0,0,16,16],2[0,8,16,16],3[15,16,16,16]. docs/p2-30-findings.md. 승격안함.

primary4보고서session20788exit0,regression/retention8보고서session38072exit0. 첫분모검사에서과거P229원본by_distance누락으로assert발생했으나기존load_report정정뷰사용후3군각12행scenario정확일치/거리별64및성공합계검증 artifacts/p2-30-scenario-pairing-audit.json. 원본수정없음.28새result영상hash/render64/camera4/step태그 artifacts/p2-30-videos-audit.json. GPUcompute없음/530GB. 대표P230영상시각검수남음.

다음P230실패단계진단(특히mixed1/2의0cm,0~2의5cm),대표영상검수,다음학습출발점고려:능력을이미잃은P229부모로부터복구대신P227부모에서직접혼합으로유지가능성. P229같은부모15전용대조를재사용가능한지계약/예산/조건검토. 아직P231프로토콜/실행없음. 전체목표미완료.


### 최신: P2-30 실패 진단 / P2-31 직접 유지 비교 시작

이전턴 P230보고서/전체평가검증은progress. P230mixed1/2 split0cm32전부유효도약미발생timeout. 실제200Hz최대상승2.953/2.496cm(<3cm),네발2N미만공중구간최대.125/.145초는있음. artifacts/p2-30-failure-gates.json,p2-30-no-flight-physics.json. mixed0/3남은0cm및mixed0~2 5cm실패는최초접촉이후안정화미달. findings추가.

P231프로토콜 docs/p2-31-protocol.md/config p2-31-mixed.json,source1e0f719. P227continuous4부모에서직접split0/15혼합800update,새4run78,643,200step. 같은부모/예산의P229split15전용대조재사용,4seed설정은목표분포/eval/tags외정확일치확인(session81580exit0). P230은출발/예산다르므로주비교에서제외.

scripts/p2_31_train.py 실행시작session96480,log artifacts/p2-31-main-batch.log. seed별P227부모split0/15×32평가→새mixed800→auto native. seed2부모retry1. 본학습은parent평가exit0후자동시작하되성공률로seed를거르지않음. 기존출력거절/부모완료감사. 다음실제PID/parent평가상태확인,부모·새모델scenario동일성/실제fork/목표별계상감사. 평가배치/3spec는미작성:신규4model continuous혼합회귀+split15×64각4(8추가),대조P229split의split혼합은P230parent평가재사용、continuous回帰/15維持はP229再使用。全体目標未完了。


### 최신: P2-31 부모 능력 확인·초기화 감사·평가 명세

이전턴P230진단/P231시작은progress. 부모split0/15×32 평가4완료감사 artifacts/p2-31-parent-audit.jsonl. 부모0cm모두32/32,15cm0/0/32/0. 따라서split에서도유지대상0cm능력을출발상태에서확인. 부모scenario와재사용P229fixed의P230parent평가scenario정확일치.

새4학습PIDs/batch1725396live,update67~74. 실제fork4감사통과 artifacts/p2-31-fork-audit.jsonl/log(session25830exit0),각관측updategoalstep합24576/resetdraw합종료수일치.

scripts/p2_31_evaluate.py 작성(아직실행안함):각새모델continuous회귀+split15×64,총8추가jobs. configs/reports/p2-31-primary/regression/retention.json 각12행(원본P2274/재사용P229fixed4/새mixed4). 코드기준20→8commands수정및출력모두spec연결검증. 각report신규학습4개만budget계상,대조군과조건별학습량800동일임을説明に維持。

다음同一本batch완료/native감사→追加8評価→3spec보고서+goal_exposure。代表P230動画視覚検収も残る。全体目標未完了。


### 최신: P2-30 대표 영상 확인 / P2-31 진행

이전턴부모검증/평가명세는progress. 이번P231batch PID1725396 live,새4run119~126update관측. P230남은대표시각검수로mixedseed1/3원본MP4의0.8초프레임ffmpeg추출후직접확인. 중앙로봇/발판렌더링및camera4유지,전체영상육안검수주장아님. artifacts/p2-30-mixed-seed1-review-0p8s.png,seed3동일파일보존. P230findings검수상태갱신.

다음동일P231batch업데이트증가/완료확인→4학습/4native감사→scripts/p2_31_evaluate.py8평가→3spec분석. 전체목표미완료.


### 최신: P2-31 본학습 완료 / 회귀평가 실행 중

이전턴영상검수는progress. 동일PID1725396 live재확인후45초단위대기,최종session96480exit0/PID없음/4seedexit0로그확인. 학습4/native4감사통과 artifacts/p2-31-training-native-audit.jsonl. goal_exposure_report총신규78,643,200step검증 docs/p2-31-primary-goal-exposure.json.

Native split0/15각32:seed0,1,2각32/32,seed3=32/0. 제자리도약은4seed모두보존,15cm동시수행은3seed만확인. 전체성공/승격주장금지. sourceconfig/보상/예산변경없음.

추가8평가 scripts/p2_31_evaluate.py 시작session83105,log artifacts/p2-31-evaluation-batch.log. 다음실제PID/세션확인·완료감사→3spec×4보고서/거리별pairing/영상hash/camera/tags/대표검수→seed3 15cm실패원인과중간거리회귀분석. 전체목표미완료.


### 최신: P2-31 전체 평가·보고서 완료

이전턴본학습완료/추가평가시작은progress. session83105exit0/PID1741683없음/4seedexit0. 추가8감사 artifacts/p2-31-additional-audit.jsonl,3평가군각12행scenario동일성/거리별합 artifacts/p2-31-pairing-audit.json 통과.

새seed0/1/2 continuous0/5/10/15각16/16,split15×64=64. seed3continuous16/16/0/0,split15=0. seed3split15유효flight15/launch반경내0/실패15timeout49,착지기록없어flight_forward=-1결측값임. docs/p2-31-findings.md. source각4조건0cm유지/15cm3seed성공,한seed실패포함.

3spec×4보고서session48642exit0. 성공episode모두최초구투영포함. 16신규resulthash/render64/camera4/phase태그 artifacts/p2-31-videos-audit.json검증. GPUcompute없음/530GB. 대표P231직접시각검수남음.

다음P232통합진단방향:동결P2314정책으로두연속도약(물리state/관절/속도reset없음) 계약설계. 단일도약대조후전환 bookkeeping/goal/launch기준/clock/접촉이력다루기. 현재JumpEnv는calibrated_root상수/episodeclock/flight와접촉latch/전역.6m이탈판정이므로단순reset재사용금지. 초기지형과범위선정/소스검토필요. 세성공seed로통합진단가능하되seed3도기록,일반성능/연속파쿠르완료주장금지. 아직P232코드/프로토콜/실행없음. 전체목표미완료.


### 최신: P2-32 두 도약 계약 / 단일 deck 대조 완료

이전턴P231결과/후속단계는progress. JumpEnv/SequentialEnv/DirectedJumpEnv/FirstTouch/FlightTravel 소스검토:현재reset이root/joint/velocity를쓰므로연속실행에재사용금지. 관측은body-frame target+velocity/joints/contact+phase/apexerror/clock. episodeclock과launchcalibration 분리필요.

docs/p2-32-protocol.md source e5d99cb:동결4정책,기존deck상대조먼저;두도약목표nominal+.15→+.30,도약당4초/전체8초,전환시실제rootXY를둘째launch기준,물리state/접촉history/직전action유지,도약별clock/latch만초기화. 매도약.3초기존PD준비,즉시반동파쿠르주장아님. 첫성공에서auto-reset억제/두번째완료만course성공,금지write/reset·tensor불변검증필수.

scripts/p2_32_deck_baseline.py실행session31819exit0,4모델deck단일15×64평가결과64/64/64/0. 기존split15시나리오정확일치,4artifact감사 artifacts/p2-32-deck-audit.jsonl. 결과는단일지형대조뿐. configs/reports/p2-32-deck-control.json8재사용학습행,보고서아직미생성.

다음구현:기존JumpEnv에기본동작동일한maneuver clock/launch reference hook→chained subclass에per-env startstep/origin/completedhop. 성공첫도약의_get_dones는reset반환억제,보상/terminalmetric snapshot후도약bookkeeping전환,physics/joints/contacts/actions보존. FlightTravel.launch는origin perenvNx2사용시new mask맞춰선택해야함(현재origin[2]만지원). 전체timestamp/segment trace/collector·감사계약별도설계. 아직두도약실행코드없음. 전체목표미완료.


### 최신: P2-32 단일 도약 회귀 검증 및 연속 도약 상태 관리

직전 카메라 설정 확인 턴은 연구 구현 기준 no progress로 분류한다. 이번 턴은 상태 관리 구현과 테스트로 progress다. c3ddca5의 maneuver_time_s/launch_reference_xy 훅을 적용한 실제 평가 artifacts/p2-32-clock-hook-regression은 이전 deck seed0와 시나리오 및 전체 episode 결과가 정확히 같다(64/64). comparison.json과 artifact 감사 passed 확인. 단일 도약 기본 동작 보존의 증거이며, 아직 두 도약 실행 증거가 아니다.

P232 deck 대조 8행 보고서와 높이/접촉/착지 후 분석 파일 생성 확인. 각 생성 로그 traceback 없음. 신규 src/parkour/chained_progress.py는 환경별 도약 완료 수, 시작 step, 출발 원점, 전환 대기, 최종 종료를 관리한다. resolve는 첫 성공의 종료를 억제하고 commit은 지표 snapshot 이후 다음 도약 시계/원점만 갱신하도록 분리했다. 실패 우선, local 200step/전체 400step 제한, 비동기 환경 전환, 완료 재집계 방지, 부분 reset, 단일 도약 계약의 3개 CPU tensor 테스트 통과(Isaac Python, artifacts/p2-32-chained-progress-tests.log). 시뮬레이터에 아직 연결하지 않았다.

다음 필수 작업: ChainedDirectedJumpEnv에서 이 상태 관리 연결, 첫 성공의 reset 억제 및 보상/지표 snapshot 이후 도약 latch만 초기화. 물리 root/joint/속도/직전 action/contact history 불변을 전환 전후 실제 tensor로 검사. 평가 adapter는 strict checkpoint restore를 유지하고 별도 chained schema, 원시 200Hz segment/target trace와 collector/audit 제공. 단일 hop 동등성→작은 2hop smoke→4seed×64 순서. 현재 GPU4장 compute 유휴, 디스크 530GB. 작업 대기 프로세스 없음. 전체 목표 미완료.


### 최신: P2-32 연속 도약 어댑터 연결 / 8환경 smoke 완료

이전 상태 관리 구현 턴은 progress. ChainedDirectedJumpEnv를 make_env/evaluate --chain-hops 1|2에 연결했다. checkpoint config/restore는 유지하고 runtime episode 기간만 4×hops초 적용한다. 첫 hop 성공은 done 반환에서 억제하고 지표 snapshot 후 latch/목표/clock/origin만 변경한다. root/joint/velocity/actions/contact hysteresis/history/episode clock/env origins 전환 전후 전체 tensor exact equality를 검사한다. 두번째 목표 nominal+.30이나 travel demand는 .15다. 원시 trace segment/startstep/target/origin 추가, chain-events.json은 첫 episode만 기록. report의 기존 비행/접촉 필드는 최종 시도 hop 진단이라고 명시, 코스 성공/완료hop histogram 별도. collector 제목에도 리셋없는 N회 도약 표기.

실제 1hop 어댑터 평가 artifacts/p2-32-chain-adapter-one-hop은 64/64, 기존 deck seed0의 모든 legacy episode 필드 정확히 동일. artifacts 감사 passed. 해당 실행은 event first-episode 필터 추가 전이나 모두 동시에 끝나므로 후속 episode 없음.

2hop 축소 artifacts/p2-32-chain-two-hop-smoke:8환경 첫 도약 성공/전환8, 코스성공0. 모두 두번째 비행 검출 시 launch 반경 .03m 위반으로 종료. 전환64step→종료96step, 전환 원점 대비 launch 이동 .05424~.05775m. 모든 보존 tensor 동일, audit passed. 이는 연속 실행 성공이 아니라 기존 정적 초기상태 정책의 전환 후 실패 관측이다. 원시200Hz 추가검사, 금지 simulator write/reset 호출 감시 보강, chain schema 독립 감사, 대표 영상검수는 남음.

다음 scripts/p2_32_chained_evaluate.py 4seed×64 원프로토콜 평가. 어떤 실패도 기준 완화로 숨기지 않는다. 추가 학습은 이 결과 및 상태분포 분석 후 별도 사전 프로토콜 필요. 전체 목표 미완료.


### 최신: P2-32 본평가 완료 및 독립 trace 감사

이전 어댑터 구현/본평가 시작 턴은 progress. session34083 exit0, 4평가 완료. scripts/audit_chained_evaluation.py 추가: hash/종료/계보 감사 후 first episode별 hop 순서/완료수/시간한도, 192전환의200Hz 전후segment/target/startstep/origin 검사 통과. artifacts/p2-32-chain-main-audit.json. seed0/1/2 첫64성공, seed3 첫0. 코스성공0/1/0/0. seed0/2 두번째64건모두launch반경위반; seed1최초접촉64정밀/시간초과63/성공1. 시간초과를 단순 안정화 실패로 확정하지 말고 travel/apex/height 등 지표 추가 분리 필요.

4result영상 hash/64render/camera4/리셋없는2회도약 제목 확인 artifacts/p2-32-chain-videos-audit.json. seed1 1.8초프레임 artifacts/p2-32-chain-seed1-review.png 직접검수. docs/p2-32-findings.md 및 chain-summary.json 작성. 전체목표미완료. 다음원시진단으로 실패단계분리→착지후초기상태 학습 대조 프로토콜. 기존 baseline과 성공 기준 유지. 금지write/reset 호출감시 보강 및 chain-events result 복사 추가는 아직 남음.


### 최신: P2-32 실패 분리 / P2-33 준비 명령 대조

이전 본평가 감사는 progress. scripts/p2_32_failure_report.py로 terminal gate 및 200Hz 준비 구간 이동량 분석, docs/p2-32-failure-diagnosis.json 생성. seed1의63timeout은 모두 FR 최종반경위반이고 나머지 주요 종료gate통과. seed0 준비이동7.38~7.53cm; seed2 3.76~4.23cm. 비행 중 종료된seed0/2의 착지gate미충족은 원인으로 취급하지 말 것.

P233사전프로토콜 docs/p2-33-protocol.md. default 준비결과 P232재사용 vs hold-last(첫성공 마지막실행action을두번째.3초준비에유지), 나머지clock/판정/정책/seed/지형불변. --chain-settle-mode 옵션 및 subclass 명령유지 구현, collector상세제목. scripts/p2_33_evaluate.py4seedbatch준비. 아직본평가시작안함.

smoke artifacts/p2-33-hold-last-smoke 실행 시작. 다음 실제process/session검사→완료감사, trace action이전환직전action과준비구간내같은지검증→4seed본평가. 전체목표미완료.


### 최신: P2-33 명령 유지 대조 완료

이전실패분석/프로토콜은progress. smoke완료(0/8), audit_chained_evaluation에준비구간실행action검사추가:전환직전action과이후.3초모든200Hz값exact일치검증. 본평가scripts/p2_33_evaluate.py session40590exit0,4seed종료. reportsession83367exit0. scripts/p2_33_report.py는대조4+실험4감사/같은checkpoint·scenario·config·지형검사후 docs/p2-33-comparison.json 생성.

첫도약event차이4seed모두0. 두도약완주hold-last모두0/64(default0/1/0/0). 준비평균이동seed0 .07430→.002114m,seed1 .04327→.005250m,seed2 .04057→.01623m. 준비명령유지가정체구간이동은줄이나완주개선없음. 모든두번째시도launch밖인지comparison필드확인가능. docs/p2-33-findings.md. 4result hash/64/camera4/상세제목검증 artifacts/p2-33-videos-audit.json. 별도학습아직시작안함.

다음연구방향:실제착지후상태분포를포함하는학습을고정예산대조. 먼저state수집/정상성/초기화계약설계; PPO기존trajectory직접replay금지. 기존P231정책부모,단일도약지형회귀필수. 현재chain은평가adapter이며training fork와보상단위/episode끝처리검증이필요하다. 성공기준완화나seed3제외금지. 전체목표미완료.


### 최신: P2-34 현재 정책의 연속 도약 학습 계약

이전P233비교완료는progress. docs/p2-34-protocol.md 사전등록: P2314부모 각각singledeck15cm vs chain15→30cm,각800×1024×24,총신규157,286,400step. 첫도약성공후같은물리상태에서현재정책으로두번째실행;저장실패trajectory replay없음. 기본PD준비.3초,기존판정/보상유지,첫성공보상은hop보상으로지급/done아님. 단일0/5/10/15회귀필수.

configs/p2-34-{single,chain}.json작성. chain_training.py는엄격한2hop/8초/fixed.15/defaultsettle/deck계약검증. restore는chain계약동일성검사; fork는검증된chain8초만4초로정규화하여부모초기화허용,지원terrain에deck추가. 임의8초/launch반경변경거부등tests/test_chain_training.py3개통과(artifacts/p2-34-contract-tests.log). make_env는trainingconfigchain선택가능, evaluate는chaincheckpoint자동평가시명시schema기록하도록chainhops추론. chained_env의Python hop/transition목록은evaluation_done존재시만쌓아학습메모리무한증가방지.

아직학습smoke/본학습시작안함. 다음필수: train로그에도약별step/성공/보상계수집추가,첫성공done억제와일회보상검증,작은fork학습/PPOfinite/checkpointresume/자동평가확인. chaincheckpoint를continuous/split단일도약회귀에쓰려면명시적single-eval override(현재chain_hops1도deck만허용)를설계하되checkpointrestore엄격성완화금지. 런타임전환의torch.equal대량sync/전체tensorclone처리비용도측정. 기존tests/test_policy_fork.py등확장회귀도실행필요. 전체목표미완료.


### 최신: P2-34 짧은 PPO 학습 및 재개 검증

이전계약설계는progress. train.py에hop별환경step/성공/reward합계추가,실제첫성공done억제assert. 기존policy_fork테스트첫실행PYTHONPATH누락실패; PYTHONPATH=src Isaac Python으로재실행4개통과 artifacts/p2-34-fork-tests-corrected.log. audit_policy_fork는systempython의rsl_rl부재로실패하므로Isaac Python사용필수.

artifacts/p2-34-chain-smoke:64env12updates/18432step 학습정상완료,artifact감사passed. 하지만hopstep[18432,0],첫성공0이므로두번째학습경로검증미완료. 재개 artifacts/p2-34-chain-smoke-resume 2updates session90922exit0:iterations13/14,steps19968/21504,감사passed. 같은config엄격복구확인. fork초기tensor독립감사는아직실행필요.

다음표본/처리량검사실행중: artifacts/p2-34-chain-profile-seed2,seed2부모fork1024env60updates,timeout600,본학습아닌별도파일럿. 다음실제worker확인→hop1/2step/PPOfinite/속도/VRAM분석. 무첫성공이면데이터도달문제를드러내고본학습검증완료로표현금지.

평가adapter도chain_hops1은continuous/split지원하도록확장(2hop은deck만). checkpointconfig/restore는그대로; 이것의실제원거리회귀평가는아직안함. make_env config8초에runtime1hop4초override. evaluate --chain-hops1 --support-modecontinuous --evaluation-forward-m0 .05 .1 .15 경로검증필요. 전체목표미완료.


### 최신: P2-34 1024환경 파일럿 완료 / 학습 후 평가 중

이전짧은smoke/재개는progress. profile동일worker1778503live확인후진행관측,session58254exit0/60updates완료. 신규1,474,560step,hopsteps[1449310,25250],hopsuccess[856,0],meanupdate.6930915초. 이는실제두번째구간PPOtransition도달증거,성능성공아님. docs/p2-34-pilot-summary.json.

IsaacPython audit_policy_fork profile/smoke둘다passed artifacts/p2-34-initialization-audit.log(관측시profile34update,초기상태검증scope). profile및초기평가완료artifact감사 artifacts/p2-34-profile-initial-audit.jsonl.

초기cp0단일continuous0/5/10/15평가 artifacts/p2-34-initial-seed2-single-regression session91884exit0:64/64,기존P231seed2regression의모든legacyepisode필드정확동일. strictchaincheckpoint+runtime1hop지원확인.

학습후cp60평가2개진행중: artifacts/p2-34-profile-seed2-chain-evaluation session85266 GPU0, artifacts/p2-34-profile-seed2-single-regression session47386 GPU2. 다음live/terminal확인→chain/일반artifact감사→거리별회귀/코스성능해석→본학습착수게이트결정. 본학습아직시작안함. currentmeanpolicy와sampled학습성공차이를혼동하지말것. 전체목표미완료.


### 최신: P2-34 파일럿 최종평가 및 본학습 착수

이전파일럿완료/평가시작은progress. sessions85266/47386완료,chain56첫성공/0완주,단일16/16/16/15. scripts/audit_chained_evaluation.py양쪽passed artifacts/p2-34-profile-evaluations-audit.json. docs/p2-34-pilot-summary.json갱신. config만지정하는자동chain평가smoke artifacts/p2-34-auto-evaluation-smoke session40171exit0/SUCCEEDED. 부모복사/재개/학습도달/finite/중간성공done억제경로확인. 파일럿은본학습증거아님.

scripts/p2_34_train.py구현:8개독립run800updates,seed짝수single→chain/홀수chain→single,각GPU1worker,본학습부모P231cp800새fork. 모든run부재/부모및smoke감사후실행. 본학습시작예정명령python3 scripts/p2_34_train.py > artifacts/p2-34-training-batch.log. 다음동일batch진행확인,학습중모델초기화감사/기본자동평가/조건별step합확인. 추가평가batch(deck1/chain2/continuousmixed/split15)아직미구현. 전체목표미완료.


### 최신: P2-34 첫 묶음 진행 / 후속 평가 32건 명세

이전본학습시작은progress. 실제worker1783928/1783929/1783942/1783943확인. 같은batchsession65779유지,현재single0/2=113update,chain1=125,chain3=106. GPU각~23~25%/3GB,설정변경없음. artifacts/p2-34-first-wave-fork-audit.log 4초기화모두passed(관측시60대update),성능완료감사아님.

scripts/p2_34_evaluate.py작성:4seed×2조건×4평가군=32유일결과참조,기존native8재사용/추가24실행. chain2deck,deck1,continuous0/5/10/15,split15모두64/진단/64render/camera4/phase태그. 전체8학습완료및native8감사후만실행. --dry-run 검증 artifacts/p2-34-evaluation-plan-dry-run.json. 아직평가batch실행안함.

발견한메타데이터표기수정:1hop mixed 평가의chain_contract.absolute_forward_targets_m가항상[.15]였으나실제episode목표/평가값은정상. 이후생성은단일고정거리일때만목록,혼합이면null+single_hop_goal_choices_m+scenario target_source명시. 과거원본artifact변경없음. 이후비교는항상scenarios와episode goal기준.

다음같은학습batch진행확인→첫묶음완료/두번째묶음시작→8학습/native감사→scripts/p2_34_evaluate.py24추가→paired분석. 전체목표미완료.


### 최신: P2-34 완료 전용 분석 코드 / 동일 학습 진행

이전평가행렬준비는progress. scripts/p2_34_report.py추가:8학습각800×24576step과총157,286,400검증,chainhop노출합계,32평가artifact/chaintrace감사,16조건짝의같은시나리오/모델경로검사,paired성공변화및거리별표생성. 아직결과파일없음. 현재미실행chainseed0 때문에의도대로중단함 artifacts/p2-34-incomplete-report-check.log;syntax검사통과. 완전한실제데이터종단검증은8학습/32평가후필요.

동일worker1783928/1783929/1783942/1783943live,251~265update확인후45초verified wait. 다음session65779동일batch유지,첫묶음800완료/native후둘째조건자동시작확인. 전체목표미완료.


### 최신: 연속 도약 result 기록 보강 / 본학습 유지

이전분석코드준비는progress. collect_results.py에chain-events.json hash검증/원자복사,manifest file/hash 및README링크추가. 기존archive에다시실행해도영상유지,이벤트충돌거부. p233seed1검증후12개완료영상archive에backfill완료(session15231exit0). 원본run/artifact변경없음.

동일4workerlive재확인후45초verifiedwait. 현재chain1=519,chain3=520,single0=544,single2=540/800. 동일batchsession65779계속,재시작/설정변경없음. 저장소530GB. 다음첫묶음완료→자동평가→둘째조건시작확인. 전체목표미완료.
