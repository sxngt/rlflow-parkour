# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: GPU 환경 수 처리량 측정 진행 중

학습4×1600 및 고정평가4 종료. 성공 seed0/1/2/3:48/64·17/64·51/64·51/64. 15cm0/3/12/16,5cm16/0/16/3 성공(각16회). seed0의15cm는비행거리미달,seed1의5cm는안정화,seed3의5cm는첫접촉정밀도실패. docs/p2-11-results.md 및 summary.json. source96d059f 학습.801/1201반경4.5/3cm reset기록네seed확인. 학습4+기본평가4+추가영상평가1 artifact감사통과,원본200Hz좌표대조통과.

64개 근접구도영상은 p2-11-curriculum-seed3__overview64-evaluation에완료, result에보존. --video-envs64 --video-camera-side4 사용,카메라거리16개와동일.첫프레임시각확인:중앙로봇식별가능,외곽일부잘림. 렌더링활성64개이지모두화면안에있다는뜻아님. 원래평가와거리별성공동일. 네기본영상포함5개보존. 사용자는64개전체를담으려고너무멀리찍지말라고지시했다.

## 현재 실행 / 다음 작업

P2-13 minibatch 비교 시작, source481b041. configs/p2-13-minibatch.json, configs/reports/p2-13.json, docs/p2-13-protocol.md. P2-12에서num_mini_batches4→32만변경(태그제외). 새정책seed0–3,각8192환경×24step×200update. minibatch6144및총gradient갱신32000은P2-11과같지만정책데이터수집빈도는200으로다름. 커리큘럼101/151에4.5/3cm,checkpoint25마다,worker1800초.

|GPU|run|session|
|---|---|---|
|0|p2-13-minibatch-seed0|80211|
|1|p2-13-minibatch-seed1|48969|
|2|p2-13-minibatch-seed2|70391|
|3|p2-13-minibatch-seed3|74163|

종료후학습4+자동평가4 audit/GPU해제확인,experiment_report.py및jump_trace_report.py configs/reports/p2-13.json. 원본200Hz/커리큘럼전환확인,거리별성공·실패·학습시간을P2-12와P2-11에비교. 개선없으면병렬규모최적화무한반복하지말고기존유효정책으로실제발판/갭경계검증단계진행. result영상4개보존.

P2-12완료:모두성공0/64·유효비행0/64·timeout64/64.학습약366–376초vsP2-11약1167–1212초였지만성공모델없으므로목표성능도달시간개선아님. 학습4+평가4감사통과,101/151반경전환확인,영상4개. docs/p2-12-results.md/summary.json 및flight-diagnosis.json.

GPU profiling완료:단독1024/2048/4096/8192 step/s38495/64367/105392/146132.8192동시합456817.학습8+평가8감사통과·영상8개. docs/gpu-env-sweep-results.md/summary.json.공통동시구간실측/CPU병목분석은미완료. GPU완전활용주장금지.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다. user요청중단전goal active유지.
