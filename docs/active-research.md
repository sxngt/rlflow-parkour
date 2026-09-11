# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: P2-09 수평 명령 범위 확장

[사전 프로토콜](p2-09-protocol.md). P2-08 travel의 보상·성공 기준을 유지하고 학습 거리만0–5cm에서0–15cm로 확장했다. 설정 비교로 거리와 태그 외 차이가 없음을 확인했다. 새 정책 네 seed, 전이 없음. source4b20205.

| GPU | 실행 | session |
|---|---|---|
| 0 | p2-09-expanded-seed0 | 25440 |
| 1 | p2-09-expanded-seed1 | 81318 |
| 2 | p2-09-expanded-seed2 | 1050 |
| 3 | p2-09-expanded-seed3 | 22516 |

각1024환경×24step×1600updates, 총157,286,400 신규step. worker 제한3600초. 자동64개 평가·16로봇 MP4·200Hz 진단. configs/p2-09-expanded.json 및 configs/reports/p2-09.json. 학습 중 설정·예산을 바꾸지 않는다. GPU는 UUID로 할당한다.

## 종료 후

1. 네 학습과 네 자동 평가의 종료·GPU 회수·hash를 audit_artifacts.py로 검사한다.
2. Isaac Python으로 experiment_report.py와 jump_trace_report.py에 configs/reports/p2-09.json을 전달한다. 원본 첫 접촉·launch/first-touch root XY 대조를 통과해야 한다.
3.0/5cm 유지와10/15cm 개선을 거리별로 구분한다. P2-08과 비교는 공통 seed0/1을 먼저 보고 seed2/3은 추가 재현성으로 보고한다.
4. 네 모델 모두 --launch-radius .03으로 엄격 재평가한다. 별도 출력 경로·태그·report spec의 evaluation_run을 지정한다. 성공한 모델만 고르지 않는다.
5. result 영상·웹 태그·현재 인계·README를 갱신한다. 실패 시 단계적 거리 커리큘럼 또는 명시적인 전이를 검토하며 동일 예산을 무한 연장하지 않는다. champion 자동 승격 없음.

## 직전 결과

[P2-08](p2-08-results.md): 동일6cm 출발 조건에서5cm 성공은 대조군0/16씩, 비행거리 보상군16/16·14/16. 보상군 제자리는16/16·10/16으로 seed1 안정화 회귀가 있다.10/15cm는 모두 실패했다.

[3cm 재평가](p2-08-strict-results.md)에서도 보상군의 위 성공이 유지됐다. 대조군은 모두0/64. 원본 좌표 대조,8개 학습/평가 및4개 엄격 평가 감사 통과. 평가영상 총8개 보존. P2-09 시작 전 GPU compute PID 없음 확인.

비행거리 보상은 첫 몸체 재접촉에 한 번만4*exp(-abs(거리-명령)/.03) 지급하며 실패·출발 위반에는0이다. 반복 접촉으로 재지급하지 않는다.34개 단위 검사와8환경 합성 착지 검사 및 짧은 학습·평가·영상 경로를 P2-08에서 검증했다. 합성 teleport 검사는 정책 성능이 아니다.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. .monitor-venv에는 NumPy가 없다. 웹 http://203.241.249.48:18710/ . 실제 갭·발판·연속 Planner·센서 적응·실기는 아직 검증하지 않았다. 평지의 목표 도약 성공을 파쿠르 완성으로 주장하지 않는다.
