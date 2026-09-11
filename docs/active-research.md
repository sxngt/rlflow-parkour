# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: GPU 환경 수 처리량 측정 진행 중

학습4×1600 및 고정평가4 종료. 성공 seed0/1/2/3:48/64·17/64·51/64·51/64. 15cm0/3/12/16,5cm16/0/16/3 성공(각16회). seed0의15cm는비행거리미달,seed1의5cm는안정화,seed3의5cm는첫접촉정밀도실패. docs/p2-11-results.md 및 summary.json. source96d059f 학습.801/1201반경4.5/3cm reset기록네seed확인. 학습4+기본평가4+추가영상평가1 artifact감사통과,원본200Hz좌표대조통과.

64개 근접구도영상은 p2-11-curriculum-seed3__overview64-evaluation에완료, result에보존. --video-envs64 --video-camera-side4 사용,카메라거리16개와동일.첫프레임시각확인:중앙로봇식별가능,외곽일부잘림. 렌더링활성64개이지모두화면안에있다는뜻아님. 원래평가와거리별성공동일. 네기본영상포함5개보존. 사용자는64개전체를담으려고너무멀리찍지말라고지시했다.

## 다음 작업

사용자GPU활용도질문에따라 docs/gpu-env-sweep-protocol.md 실행:1024/2048/4096/8192환경각100update(앞20warmup),동일GPU순차단독측정후선정규모4GPU동시측정. scripts/profile_env_sweep.py로GPU0 순차 단독 측정을 시작했다. driver session99735, artifacts/gpu-env-sweep-driver.log, source7f4ec47. 1024→2048→4096→8192 각100update와자동평가. 새실행중복시작금지. .host-profile.jsonl에2초주기GPU/CPU누적시간/RSS/I/O/호스트메모리·디스크여유와training_status/iteration수집. STARTING/RUNNING/SUCCEEDED로학습과후속평가구간구분. .monitor-venv에psutil7.2.2사용. 기존평가16로봇영상은각실행별유지. 측정구간과자동평가/렌더구간분리. 다음제어실험은측정결과와P2-11실패분석후결정하며동일학습무한연장금지.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다. user요청중단전goal active유지.
