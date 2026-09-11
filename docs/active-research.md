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
