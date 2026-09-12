# P2-40 단일 목표 선택 비중 비교

P2-39 균등 대조78,643,200step을 재사용하고 가중치 조건78,643,200step을 새로 학습했다.

| seed | 평가군 | 균등 선택 /64 | 1:1:1:3 선택 /64 |
|---|---|---|---|
| 0 | chain | 64 | 64 |
| 0 | deck-regression | 64 | 64 |
| 0 | regression | 64 | 64 |
| 0 | split15 | 0 | 0 |
| 1 | chain | 0 | 64 |
| 1 | deck-regression | 48 | 64 |
| 1 | regression | 48 | 64 |
| 1 | split15 | 0 | 64 |
| 2 | chain | 0 | 64 |
| 2 | deck-regression | 46 | 61 |
| 2 | regression | 46 | 61 |
| 2 | split15 | 0 | 64 |
| 3 | chain | 0 | 0 |
| 3 | deck-regression | 16 | 20 |
| 3 | regression | 16 | 20 |
| 3 | split15 | 0 | 0 |
