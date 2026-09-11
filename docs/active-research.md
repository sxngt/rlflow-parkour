# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: GPU 환경 수 처리량 측정 진행 중

학습4×1600 및 고정평가4 종료. 성공 seed0/1/2/3:48/64·17/64·51/64·51/64. 15cm0/3/12/16,5cm16/0/16/3 성공(각16회). seed0의15cm는비행거리미달,seed1의5cm는안정화,seed3의5cm는첫접촉정밀도실패. docs/p2-11-results.md 및 summary.json. source96d059f 학습.801/1201반경4.5/3cm reset기록네seed확인. 학습4+기본평가4+추가영상평가1 artifact감사통과,원본200Hz좌표대조통과.

64개 근접구도영상은 p2-11-curriculum-seed3__overview64-evaluation에완료, result에보존. --video-envs64 --video-camera-side4 사용,카메라거리16개와동일.첫프레임시각확인:중앙로봇식별가능,외곽일부잘림. 렌더링활성64개이지모두화면안에있다는뜻아님. 원래평가와거리별성공동일. 네기본영상포함5개보존. 사용자는64개전체를담으려고너무멀리찍지말라고지시했다.

## 현재 실행 / 다음 작업

P2-12 대규모 batch 동일step 비교 시작. docs/p2-12-protocol.md, configs/p2-12-large-batch.json, configs/reports/p2-12.json. source8e5b321. 새정책seed0–3,각8192환경×24step×200updates=39,321,600step(P2-11과같음).커리큘럼101/151update에서4.5/3cm전환,checkpoint25마다,worker1800초. PPO batch8배/update수1/8,환경reset표본차이명시. 아직성능결과없음.

|GPU|run|session|
|---|---|---|
|0|p2-12-large-batch-seed0|6334|
|1|p2-12-large-batch-seed1|80604|
|2|p2-12-large-batch-seed2|45086|
|3|p2-12-large-batch-seed3|93589|

종료후학습4+자동평가4 audit,GPU해제확인. experiment_report.py 및jump_trace_report.py configs/reports/p2-12.json.101/151반경전환검사,원본200Hz좌표대조. P2-11(48/17/51/51성공)과거리별/seed별성능·시간·환경step비교. result영상4개보존. 실패하면8192를처리량만으로채택하지말고4096또는minibatch구조별도검토. 중간결과로예산변경금지.

완료profiling:단독1024/2048/4096/8192 step/s38495/64367/105392/146132.8192동시113419/114704/114231/114462합456817(개별구간합). 학습8+평가8감사통과·영상8개. docs/gpu-env-sweep-results.md/summary.json 및script. 공통동시구간실측진행량/CPU병목분석은미완료로남음. GPU사용률최대화완료주장금지.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다. user요청중단전goal active유지.
