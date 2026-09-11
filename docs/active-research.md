# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: GPU 환경 수 처리량 측정 진행 중

학습4×1600 및 고정평가4 종료. 성공 seed0/1/2/3:48/64·17/64·51/64·51/64. 15cm0/3/12/16,5cm16/0/16/3 성공(각16회). seed0의15cm는비행거리미달,seed1의5cm는안정화,seed3의5cm는첫접촉정밀도실패. docs/p2-11-results.md 및 summary.json. source96d059f 학습.801/1201반경4.5/3cm reset기록네seed확인. 학습4+기본평가4+추가영상평가1 artifact감사통과,원본200Hz좌표대조통과.

64개 근접구도영상은 p2-11-curriculum-seed3__overview64-evaluation에완료, result에보존. --video-envs64 --video-camera-side4 사용,카메라거리16개와동일.첫프레임시각확인:중앙로봇식별가능,외곽일부잘림. 렌더링활성64개이지모두화면안에있다는뜻아님. 원래평가와거리별성공동일. 네기본영상포함5개보존. 사용자는64개전체를담으려고너무멀리찍지말라고지시했다.

## 현재 실행 / 다음 작업

단독측정1024/2048/4096/8192 모두학습100+평가완료. warmup20제외step/s38495/64367/105392/146132,2초표본학습peakVRAM3085/3431/4061/5341MiB. 학습4+평가4감사통과. docs/gpu-env-sweep-protocol.md.

8192환경4GPU동시측정시작, source e09ecf2. label concurrent-gpu0~3. 각seed0,100updates,별도독립정책. --skip-final-evaluation으로전체학습종료전렌더링간섭제외. scripts/profile_env_sweep.py wrapper와run_job.py worker의PID실제확인하여중복실행금지.

|GPU|session|driver log|
|---|---|---|
|0|62981|artifacts/gpu-env-sweep-concurrent-gpu0-driver.log|
|1|98410|artifacts/gpu-env-sweep-concurrent-gpu1-driver.log|
|2|77817|artifacts/gpu-env-sweep-concurrent-gpu2-driver.log|
|3|56817|artifacts/gpu-env-sweep-concurrent-gpu3-driver.log|

출력 artifacts/gpu-env-sweep-n8192-concurrent-gpuN. .host-profile.jsonl 2초GPU+CPU시간/RSS/I/O/호스트메모리/디스크,training_iteration/status. 종료후학습4audit하고전체GPU해제확인후각checkpoint-000100.pt 평가·영상(16개기본)을 별도 __final-evaluation에실행해야한다. 동일config configs/profiling/env-8192.json, seed0. 이후집계보고서작성:개별step/s,합계,단독대비slowdown,전체동시구간의실측진행량,VRAM/CPU/RAM/I/O. sampler4개호출부하차이제한표시. 각표본training_status=RUNNING이며iteration20이후인구간으로학습집계,초기화/평가분리. 최종연구배치규모는아직미확정이며PPO batch변화의학습효과별도검증필요.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다. user요청중단전goal active유지.
