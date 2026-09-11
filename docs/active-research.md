# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: GPU 환경 수 처리량 측정 진행 중

학습4×1600 및 고정평가4 종료. 성공 seed0/1/2/3:48/64·17/64·51/64·51/64. 15cm0/3/12/16,5cm16/0/16/3 성공(각16회). seed0의15cm는비행거리미달,seed1의5cm는안정화,seed3의5cm는첫접촉정밀도실패. docs/p2-11-results.md 및 summary.json. source96d059f 학습.801/1201반경4.5/3cm reset기록네seed확인. 학습4+기본평가4+추가영상평가1 artifact감사통과,원본200Hz좌표대조통과.

64개 근접구도영상은 p2-11-curriculum-seed3__overview64-evaluation에완료, result에보존. --video-envs64 --video-camera-side4 사용,카메라거리16개와동일.첫프레임시각확인:중앙로봇식별가능,외곽일부잘림. 렌더링활성64개이지모두화면안에있다는뜻아님. 원래평가와거리별성공동일. 네기본영상포함5개보존. 사용자는64개전체를담으려고너무멀리찍지말라고지시했다.

## 현재 실행 / 다음 작업

모든profiling학습8개와평가8개종료·감사통과. GPU별8192동시 처리량113419/114704/114231/114462step/s,합456817(개별구간합,동기화makespan과다름). 단독8192는146132. 평균GPU약28%,표본VRAM약5.2GiB. docs/gpu-env-sweep-results.md/summary.json 및 scripts/gpu_profile_report.py. .host-profile.jsonl 원본에CPU/RSS/I/O포함. 추가과제:공통동시구간처리량을표본진행으로집계하고CPU병목분석. 순간snapshot이나VRAM만으로완전활용주장금지.

다음제어실험은총환경step을P2-11과맞춰8192환경×24step×200updates로검토한다(각39,321,600step).6/4.5/3cm커리큘럼경계100/150으로변경하면노출step비율동일. PPO batch8배·optimizerupdate수1/8의학습효과를명시적으로비교해야하며성능향상미검증. 아직P2-12 config/protocol/실행없음. 사전프로토콜작성후seed0–3실행하고원래1024조건과같은고정64평가·result영상. 실제갭·발판단계진행이라는원래목표유지.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다. user요청중단전goal active유지.
