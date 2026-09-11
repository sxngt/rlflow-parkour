# P2-15 최초 착지 지지면 진단

거리 0/5/10/15cm × 높이 명령 16개의 동일 개발군을 사용한다. 원시 200Hz 최초 접촉 오차를 저장된 KPI와 1e-5m 이내로 대조했다.

| 조건 | seed | 기존 성공 / 64 | 첫 접촉 네 발 투영 포함 | 성공과 포함 모두 |
|---|---:|---:|---:|---:|
| flat-train → flat-eval | 0 | 0 | 64 | 0 |
| flat-train → deck-eval | 0 | 0 | 43 | 0 |
| flat-train → flat-eval | 1 | 0 | 0 | 0 |
| flat-train → deck-eval | 1 | 0 | 0 | 0 |
| flat-train → flat-eval | 2 | 10 | 64 | 10 |
| flat-train → deck-eval | 2 | 11 | 57 | 11 |
| flat-train → flat-eval | 3 | 17 | 64 | 17 |
| flat-train → deck-eval | 3 | 0 | 13 | 0 |
| deck-train → flat-eval | 0 | 0 | 0 | 0 |
| deck-train → deck-eval | 0 | 0 | 0 | 0 |
| deck-train → flat-eval | 1 | 0 | 0 | 0 |
| deck-train → deck-eval | 1 | 0 | 0 | 0 |
| deck-train → flat-eval | 2 | 0 | 64 | 0 |
| deck-train → deck-eval | 2 | 0 | 64 | 0 |
| deck-train → flat-eval | 3 | 48 | 64 | 48 |
| deck-train → deck-eval | 3 | 48 | 64 | 48 |

포함은 발 중심 높이 2±1cm 및 발판 가장자리에서 2cm 여유를 확인한 기하 진단이다. 실제 접촉 쌍이나 착지 이후 지지 지속을 보장하지 않는다. 평지에는 XY 경계가 없다. 이 진단은 기존 성공 정의를 소급 변경하지 않는다.
