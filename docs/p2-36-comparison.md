# P2-36 단일 과제 혼합의 고정 예산 비교

신규 혼합 학습 78,643,200 step. 대조군 P2-34의 같은 예산 결과를 재사용했다.

| seed | 평가군 | 연속 전용 /64 | 단일 과제 혼합 /64 |
|---|---|---|---|
| 0 | chain | 0 | 64 |
| 0 | deck-single | 0 | 64 |
| 0 | regression | 0 | 48 |
| 0 | split15 | 0 | 0 |
| 1 | chain | 64 | 4 |
| 1 | deck-single | 64 | 9 |
| 1 | regression | 16 | 32 |
| 1 | split15 | 0 | 0 |
| 2 | chain | 0 | 61 |
| 2 | deck-single | 0 | 64 |
| 2 | regression | 17 | 0 |
| 2 | split15 | 0 | 0 |
| 3 | chain | 0 | 1 |
| 3 | deck-single | 0 | 64 |
| 3 | regression | 0 | 16 |
| 3 | split15 | 0 | 0 |

동일 seed/시나리오의 개발군 비교이며, 최종 모델 승격이나 최종 시험 성공을 의미하지 않는다.
