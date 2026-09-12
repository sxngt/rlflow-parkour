# P2-39 단일 과제의 목표 거리 범위 비교

P2-38 두 거리 대조78,643,200step을 재사용하고 네 거리 조건78,643,200step을 새로 학습했다.

| seed | 평가군 | 0·15cm 학습 /64 | 0·5·10·15cm 학습 /64 |
|---|---|---|---|
| 0 | chain | 64 | 64 |
| 0 | deck-regression | 64 | 64 |
| 0 | regression | 64 | 64 |
| 0 | split15 | 0 | 0 |
| 1 | chain | 42 | 0 |
| 1 | deck-regression | 64 | 48 |
| 1 | regression | 64 | 48 |
| 1 | split15 | 64 | 0 |
| 2 | chain | 63 | 0 |
| 2 | deck-regression | 48 | 46 |
| 2 | regression | 48 | 46 |
| 2 | split15 | 64 | 0 |
| 3 | chain | 0 | 0 |
| 3 | deck-regression | 48 | 16 |
| 3 | regression | 48 | 16 |
| 3 | split15 | 64 | 0 |
