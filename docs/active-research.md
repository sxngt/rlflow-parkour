# 현재 연구 인계

사용자가 중단할 때까지 연구 goal은 active다. 실제 프로세스·GPU·artifact를 확인하고, 이전 상태만으로 중복 실행하지 않는다.

## 현재: P2-10 · 3cm 출발 직접 학습

[프로토콜](p2-10-protocol.md). P2-09와 출발 범위0.06→0.03 및 태그 외 설정이 같음을 assert했다. 새 정책 seed0–3, 전이 없음. source f8f5264.

| GPU | 실행 | session |
|---|---|---|
|0|p2-10-strict-seed0|46120|
|1|p2-10-strict-seed1|77802|
|2|p2-10-strict-seed2|63931|
|3|p2-10-strict-seed3|91065|

각1024환경×24step×1600updates. 총157,286,400 신규step. worker3600초. 자동64개 평가·16로봇 MP4·200Hz 진단. configs/p2-10-strict.json 및 configs/reports/p2-10.json. 중간 결과로 예산·설정을 바꾸지 않는다.

## 종료 후

1. 네 학습 및 네 자동 평가 실제 PID 종료·GPU 해제 확인, audit_artifacts.py로 hash 검사.
2. Isaac Python으로 experiment_report.py 및 jump_trace_report.py configs/reports/p2-10.json 실행. 원본 launch/first-touch 좌표 대조를 통과해야 한다.
3. P2-09-strict와 같은3cm 평가조건에서 거리별·seed별 비교. 제자리/5cm 능력 유지와10/15cm 개선 및 출발·비행거리·첫 접촉·안정화 실패를 분리.
4. result 영상·웹 태그·문서 갱신. 실패하면 출발 조건 커리큘럼/명시적 전이 등 검토, 같은 예산 무한 연장 금지. champion 자동 승격 없음.

## 직전 결과 P2-09

6cm 학습/평가 성공은 seed0/1/2/3:63/64·50/64·62/64·55/64. 15cm는 모두16/16,10cm는16/16·16/16·16/16·7/16. 제자리는15/16·2/16·14/16·16/16으로 회귀가 있다. 모든 거리의 첫 접촉 정밀도와 비행거리 조건은 모두 통과했고 실패는 안정화였다.

3cm 실제 재평가 성공32/64·18/64·33/64·32/64. 15cm는 모두 출발 범위 위반으로0/16. 5cm는 모두16/16 유지.10cm는 seed0/2만16/16. 15cm 비행 확인 시 calroot 대비 XY 이동은 seed별 약4.89–4.92,5.12–5.25,4.58–4.64,5.09–5.12cm. 이는 정확한 이륙 순간이나 순수 지면 이동량이 아니다.

학습4+기본평가4+엄격평가4 감사와 원본200Hz 좌표 대조 통과. 영상8개 보존. 결과 docs/p2-09-results.md 및 docs/p2-09-strict-results.md. P2-10 시작 전 GPU compute PID 없음 확인.

## 환경과 범위

Isaac Python /mnt/sdb1/sxngt/isaac-sim-4.5.0/python.sh. .monitor-venv에는 NumPy가 없다. 웹 http://203.241.249.48:18710/ . 실제 갭·발판·연속 Planner·센서 적응·실기는 아직 검증하지 않았다. 평지의 목표 도약 성공을 파쿠르 완성으로 주장하지 않는다.
