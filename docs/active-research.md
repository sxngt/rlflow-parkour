# 현재 연구 인계

## 현재 작업: P2-08 완료, 다음 거리 확장 실험 준비

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


## P2-08 완료 결과 (이 문단이 위 실행중 기록보다 최신)

네 main학습 및 네 final-evaluation 모두완료,8run감사·원본좌표대조통과.6cm에서대조성공16/16,보상32/24(각64평가). 보상군0cm16/16과10/16,5cm16/16과14/16. 대조5cm모두0/16.10/15cm전부실패. seed1제자리안정화회귀가있어모든능력향상이라고주장하지않는다. result영상4개보존. docs/p2-08-results.md.

추가학습없이전4모델의3cm strict-evaluation도완료. 대조0/0,보상32/24로보상군성공유지. artifacts/p2-08-strict-audit.jsonl, docs/p2-08-strict-results.md. strict재평가영상4개보존. 기존모델승격없음. 모든학습은종료됐으므로중복재시작하지않는다.

다음은0–5cm능력의seed확인과0–15cm명령범위확장. 후보:동일travel보상4에서0–15cm신규학습,4seed고정예산,0/5cm회귀와10/15cm성공평가. 아직새프로토콜/새학습없음. 성공범위가작으므로실제발판·갭성공을아직주장하지않으며향후실제geometry도입이필수다. 원본첫접촉정밀·실비행거리·출발·안정화기준유지. P2-08시작당시session들은모두종료됐고재평가도완료상태를확인한뒤다음작업으로진행한다.
