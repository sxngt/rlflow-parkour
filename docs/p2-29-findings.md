# P2-29 결과와 남은 검증

P2-27 네 부모 정책 각각에서 continuous/split 추가학습을 같은 예산으로 수행했다. 신규 학습은 8 × 1024환경 × 24step × 800update = 157,286,400step이다. 부모 학습량은 별도이며 이번 예산에 중복 합산하지 않는다. 단일 15cm 목표의 개발군 결과이고, 실제 발별 발판 간 빈 공간은 6cm다. 연속 코스·Planner·실기 성능을 의미하지 않는다.

| 학습 조건 / 평가 | seed 0 | seed 1 | seed 2 | seed 3 |
|---|---:|---:|---:|---:|
| 부모 / continuous 15cm | 0 | 0 | 64 | 0 |
| 부모 / split 15cm | 0 | 0 | 64 | 0 |
| continuous 추가학습 / continuous 15cm | 64 | 64 | 64 | 64 |
| continuous 추가학습 / split 15cm | 15 | 64 | 64 | 64 |
| split 추가학습 / continuous 15cm | 64 | 64 | 64 | 64 |
| split 추가학습 / split 15cm | 64 | 64 | 64 | 64 |

각 칸의 분모는 동일한 높이 명령 64개다. 부모 대비 추가학습 후 목표 수행은 개선됐으나, split 학습의 추가 이득은 이번 네 seed 중 seed 0의 split 전이에 집중됐다. 모든 seed에 동일한 지형 효과가 있었다고 주장하지 않는다.

continuous의 0/5/10/15cm 회귀군에서는 모든 새 모델의 5/10/15cm가 각각16/16이었다. 0cm 성공은 continuous 추가학습 16/0/0/0, split 추가학습 16/1/0/0이다. 부모는 0cm에서 모두16/16이었다. 따라서 seed1~3의 제자리 도약 능력 회귀가 있으며 champion 승격 조건을 충족했다고 볼 수 없다.

평가 16개 교차/회귀 및 8개 native, 학습 8개의 완료 무결성 감사는 통과했다. 보고서는 primary와 regression 두 명세별로 학습 곡선·원시 최초 접촉·지지면 투영·착지 후 목표 유지 진단을 생성했다. 후속 검토는 0cm의 실패 원인과 continuous seed0의 split 전이 실패를 원시 trace에서 분리하는 것이다. 혼합 목표 학습을 도입한다면 split의 0–15cm 연속 샘플링은 갭 위의 불가능한 목표를 만들므로 사용하지 않는다.

## 거리별 요약 오류와 처리

평가 전용 거리 override는 실제 시나리오와 개인별 기록을 올바르게 변경했으나, evaluation.json의 by_distance는 학습 config의15cm만 순회했다. 전체성공수와 개별episode는 영향을 받지 않았다. 원본을 수정하지 않고 `evaluation_summary.load_report`가 실제 scenario ID·거리 일치를 검사해 네 거리 요약을 재계산한다. 정정된 보고서에는 원본 evaluation/scenario hash 및 원래 요약을 남긴다. `artifacts/p2-29-derived-distance-summary.json`도 보존한다. 다음 평가부터는 생성 시 동일 집계 함수를 사용한다. 집계·누락/중복/잘못된 거리 거절·원본 불변 테스트2개 통과. 모니터링 API의 과거 by_distance 표시 보정은 후속 작업으로 남아 있다.

새 교차/회귀 영상16개의 result hash·구도·태그와 대표 영상 시각 검수는 아직 별도 확인이 필요하다. GPU compute process는 배치 종료 후 없어졌으며 저장소 여유는 약531GB였다.
