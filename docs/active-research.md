# 현재 연구 인계

## 현재 작업: P2-08 최초 착지 비행거리 보상

사용자 중단 전까지 goal active. [프로토콜](p2-08-protocol.md). P2-07 short의5cm 비행 이동1.47–1.82cm 부족을 개선하기 위한 보상0/4 비교. 두 조건 모두0–5cm학습·6cm출발·나머지성공기준동일. 최초몸체재접촉시한번만4*exp(-abs(실비행거리-명령)/.03). 실패·출발영역위반에는0,나중에회복해도재지급없음.

| GPU | run | session |
|---|---|---|
| 0 | p2-08-control-seed0 | 다음 실제 PID 확인 |
| 1 | p2-08-control-seed1 | 다음 실제 PID 확인 |
| 2 | p2-08-travel-seed0 | 다음 실제 PID 확인 |
| 3 | p2-08-travel-seed1 | 다음 실제 PID 확인 |

각1024환경×24step×1600updates, 총157,286,400신규step. worker3600초. 자동64평가·16로봇MP4·200Hz진단. configs/p2-08-{control,travel}.json, report configs/reports/p2-08.json. 실행중기준변경/중복실행금지. 현재메인학습시작됨.

검증:34개단위검사(artifacts/p2-08-unit-tests.log),8env합성착지의1회지급검사(p2-08-travel-state-check.log),64env2update3072step+자동평가영상,2run감사(p2-08-implementation-audit.jsonl)통과. 합성teleport검사는정책성능아님. main전GPUcompute없음확인. source bcd4f45 + 합성검사추가commit.

완료후8run감사→experiment_report.py/jump_trace_report.py configs/reports/p2-08.json→원본좌표대조→거리별성과/회귀분석→result영상/웹태그/인계갱신.6cm결과를3cm성공으로간주하지않고필요시전모델--launch-radius .03 재평가. 자동champion승격없음. 평가에서첫실비행보상값은현재terminal_metrics에있지만evaluation.json의선별필드에는없음; 성능은거리·접촉·안정화로검증.

## 직전 결과

P2-07은6cm에서모든정책비행64/64. zero성공0/31, short16/16. short는0cm만성공. 3cm재평가에서도zero seed1만0cm15/16·5cm16/16성공유지,다른세모델0. 단일seed전이이며일반수평Tracker완성아님. docs/p2-07-results.md 및 p2-07-strict-results.md에전체기록. 평가override는checkpoint원계약restore검사후평가에만적용하며기록된다.

## 환경

IsaacPython /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. .monitor-venv NumPy없음. 웹 http://203.241.249.48:18710/ .4GPUUUID할당run_job.py. 전체이력p0-status.md. 실제갭·Planner·실기아직미검증.
