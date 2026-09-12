# P2-27-PARTIAL 최초 착지 지지면 진단

거리 0/5/10/15cm × 높이 명령 16개의 동일 개발군을 사용한다. 원시 200Hz 최초 접촉 오차를 저장된 KPI와 1e-5m 이내로 대조했다.

| 조건 | seed | 기존 성공 / 64 | 첫 접촉 네 발 투영 포함 | 성공과 포함 모두 |
|---|---:|---:|---:|---:|
| train-deck_eval-deck | 0 | 56 | 64 | 56 |
| train-deck_eval-deck | 1 | 32 | 64 | 32 |
| train-deck_eval-deck | 3 | 21 | 64 | 21 |
| train-deck_eval-continuous | 0 | 0 | 0 | 0 |
| train-deck_eval-continuous | 1 | 0 | 0 | 0 |
| train-deck_eval-continuous | 3 | 0 | 0 | 0 |
| train-continuous_eval-continuous | 0 | 48 | 64 | 48 |
| train-continuous_eval-continuous | 1 | 48 | 64 | 48 |
| train-continuous_eval-continuous | 3 | 48 | 64 | 48 |
| train-continuous_eval-deck | 0 | 48 | 64 | 48 |
| train-continuous_eval-deck | 1 | 48 | 64 | 48 |
| train-continuous_eval-deck | 3 | 48 | 64 | 48 |

포함은 발 중심 높이 2±1cm 및 발판 가장자리에서 2cm 여유를 확인한 기하 진단이다. 실제 접촉 쌍이나 착지 이후 지지 지속을 보장하지 않는다. 평지에는 XY 경계가 없다. 이 진단은 기존 성공 정의를 소급 변경하지 않는다.
