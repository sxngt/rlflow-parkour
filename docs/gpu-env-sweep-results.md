# GPU 환경 수 처리량 측정

동일100update 중 처음20회를 제외한80회. 학습 수렴 속도나 제어 성능을 증명하는 비교가 아니다.

| 실행 | 환경 | step/s | GPU 평균 사용률 | 표본 최대 VRAM(MiB) | 평균 전력(W) |
|---|---:|---:|---:|---:|---:|
| gpu-env-sweep-n1024-solo | 1024 | 38495 | 27.2% | 3085 | 82.2 |
| gpu-env-sweep-n2048-solo | 2048 | 64367 | 28.1% | 3431 | 85.5 |
| gpu-env-sweep-n4096-solo | 4096 | 105392 | 32.2% | 4061 | 93.3 |
| gpu-env-sweep-n8192-solo | 8192 | 146132 | 35.1% | 5341 | 106.2 |
| gpu-env-sweep-n8192-concurrent-gpu0 | 8192 | 113419 | 28.4% | 5370 | 94.3 |
| gpu-env-sweep-n8192-concurrent-gpu1 | 8192 | 114704 | 28.4% | 5332 | 94.5 |
| gpu-env-sweep-n8192-concurrent-gpu2 | 8192 | 114231 | 28.0% | 5334 | 93.4 |
| gpu-env-sweep-n8192-concurrent-gpu3 | 8192 | 114462 | 28.1% | 5351 | 96.9 |

동시 실행의 개별 처리량 합은 456817step/s이다. 동기화된 makespan 처리량과 구분한다.

단독 환경 수당 한 번의 짧은 측정이며 PPO batch가 달라진다. 자원 수치는 약2초 간격 표본이며 진짜 순간 최대값이 아니다. CPU·I/O는 호스트 전체 서비스가 포함된다. 동시 측정은 sampler4개로 호출 부하도 증가한다. 원본·추가 지표는 gpu-env-sweep-summary.json 및 artifacts/*.host-profile.jsonl 참조.
