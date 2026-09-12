# P2-29 최초 착지 지지면 진단

거리 15cm × 높이 명령 64개의 동일 개발군을 사용한다. 원시 200Hz 최초 접촉 오차를 저장된 KPI와 1e-5m 이내로 대조했다.

| 조건 | seed | 기존 성공 / 64 | 첫 접촉 네 발 투영 포함 | 성공과 포함 모두 |
|---|---:|---:|---:|---:|
| parent-on-continuous | 0 | 0 | 64 | 0 |
| parent-on-split | 0 | 0 | 0 | 0 |
| train-continuous_eval-continuous | 0 | 64 | 64 | 64 |
| train-continuous_eval-split | 0 | 15 | 0 | 0 |
| train-split_eval-continuous | 0 | 64 | 64 | 64 |
| train-split_eval-split | 0 | 64 | 64 | 64 |
| parent-on-continuous | 1 | 0 | 64 | 0 |
| parent-on-split | 1 | 0 | 64 | 0 |
| train-continuous_eval-continuous | 1 | 64 | 64 | 64 |
| train-continuous_eval-split | 1 | 64 | 64 | 64 |
| train-split_eval-continuous | 1 | 64 | 64 | 64 |
| train-split_eval-split | 1 | 64 | 64 | 64 |
| parent-on-continuous | 2 | 64 | 64 | 64 |
| parent-on-split | 2 | 64 | 64 | 64 |
| train-continuous_eval-continuous | 2 | 64 | 64 | 64 |
| train-continuous_eval-split | 2 | 64 | 64 | 64 |
| train-split_eval-continuous | 2 | 64 | 64 | 64 |
| train-split_eval-split | 2 | 64 | 64 | 64 |
| parent-on-continuous | 3 | 0 | 64 | 0 |
| parent-on-split | 3 | 0 | 64 | 0 |
| train-continuous_eval-continuous | 3 | 64 | 64 | 64 |
| train-continuous_eval-split | 3 | 64 | 64 | 64 |
| train-split_eval-continuous | 3 | 64 | 64 | 64 |
| train-split_eval-split | 3 | 64 | 64 | 64 |

포함은 발 중심 높이 2±1cm 및 발판 가장자리에서 2cm 여유를 확인한 기하 진단이다. 실제 접촉 쌍이나 착지 이후 지지 지속을 보장하지 않는다. 평지에는 XY 경계가 없다. 이 진단은 기존 성공 정의를 소급 변경하지 않는다.
