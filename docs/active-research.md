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
