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
