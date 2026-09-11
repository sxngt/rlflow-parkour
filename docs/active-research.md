# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: P2-11 출발 범위 커리큘럼 학습 중

프로토콜 docs/p2-11-protocol.md, config configs/p2-11-curriculum.json, 보고서 configs/reports/p2-11.json. source96d059f. 새 정책 네 seed(전이 없음), 총157,286,400step, 각1024환경×24step×1600updates.

| GPU | run | session |
|---|---|---|
|0|p2-11-curriculum-seed0|77745|
|1|p2-11-curriculum-seed1|67965|
|2|p2-11-curriculum-seed2|40922|
|3|p2-11-curriculum-seed3|49443|

1–800update6cm,801–1200은4.5cm,1201–1600은3cm. 경계에서 모든 env reset, 미완료episode 통계 제외. final config 반경은3cm이고 평가에서는 schedule을 적용하지 않는다. checkpoint에 완료update·다음반경·전환계약 저장, restore시검사. 학습 metrics에 launch_radius_m 및 curriculum_reset_all 기록.

37개 단위 검사 통과. 첫 smoke는 inference tensor 외부 reset 오류로실패하여 보존했다. 수정후 p2-11-smoke-fixed 3updates(6→4.5→3), checkpoint1에서 p2-11-resume-check 2updates(4.5→3) 성공. 두 자동평가·영상 포함4artifact감사통과. checkpoint상태3cm확인. 검증은 성능 결과가 아니다.

## 종료 후

사용자가64개 렌더링을 요청했다. evaluate.py에 --video-envs64 옵션이 이미 있으며 ParallelRecorder가8×8 배치/먼 카메라를 지원한다. P2-11 자동16개 평가 종료 후 별도출력 __overview64-evaluation에서 --video --video-envs64 --diagnostics로 고정모델 평가를 실행하고 result에 보존할 것. 현재1280×720이므로 실제 첫프레임에서64개가 보이는지와 식별성을 확인한다. 필요시 해상도 옵션을 추가하며 학습run은 변경하지 않는다.


사용자의 GPU 활용도 질문에 따라 P2-11 완료/평가 다음에는 docs/gpu-env-sweep-protocol.md의1024→2048→4096→8192 환경 처리량 측정을 우선 실행한다. 현재 학습 설정은 유지. 단독/4GPU 동시 실행의 실제 처리량과 호스트 병목을 측정한 후 다음 연구 규모를 정한다.

실제PID종료 및GPU해제확인, 학습4+평가4 audit. IsaacPython scripts/experiment_report.py와 scripts/jump_trace_report.py configs/reports/p2-11.json 실행. 801/1201반경전환과reset기록을 확인한다. 원본200Hz launch/first-touch좌표 대조. P2-10 및 P2-09-strict와 같은3cm 평가에서 거리별·seed별 비교. result영상·웹태그·문서갱신. 자동champion승격없음. 실패시동일예산무한연장금지.

## 직전 P2-10

모두1600학습/64평가종료, 성공0/64·유효비행0/64·timeout64/64. 제어경계몸체상승3cm모두미달(각seed최대약1.66/2.10/2.07/2.20cm). 비접촉window와상승속도는있었음. docs/p2-10-results.md 및 flight-diagnosis.md/json. 8artifact감사통과·영상4개보존. P2-09-strict는성공32/18/33/32였고15cm모두출발범위위반. 직접엄격조건학습의다른실패양상이다.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. 웹 http://203.241.249.48:18710/ . GPU4장시작전compute PID없음확인. 실제갭·발판·Planner·센서적응·실기미검증. 평지목표도약을파쿠르완성으로주장하지않는다.
