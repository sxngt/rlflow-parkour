# GPU 환경 수 처리량 측정

P2-11 종료 및 고정 평가 후 수행한다. 현재 비교 실험의 환경 수·batch는 변경하지 않는다. 사용자 질문에서 확인한 단일 시점 GPU22–28%, VRAM약3GB/24GB는 최대 처리량을 검증한 결과가 아니다.

동일 directed-jump 설정의 num_envs만1024,2048,4096,8192로 바꾼 별도 run을 만든다. 각100 PPO update, 처음20회는 warmup으로 분리하고 나머지80회의 step/s·update당 시간 및 변동을 보고한다. 동일 seed0 사용. 초기화 시간은 전체 wall-clock과 별도로 표시한다. 짧은 성능 측정은 수렴 또는 제어 성능 비교가 아니다. 환경 수 변경은 PPO batch도 변경하므로 여기서 빠른 설정을 곧바로 기존 연구 비교군에 섞지 않는다.

먼저 동일 GPU에서 네 크기를 순차 단독 실행한다. 가능성이 있는 규모를 선정한 후 네 GPU에 같은 크기의 독립 run을 동시에 배치해 전체 step/s와 단독 대비 slowdown을 확인한다. 최종 규모는 측정 전 확정하지 않는다. OOM이면 실패와 peak 관측값을 보존하고 해당 크기를 무한 재시도하지 않는다.

GPU UUID·VRAM peak·utilization·전력, worker 및 자식 프로세스 CPU/RSS, 호스트 RAM·I/O·디스크 여유를 실행 구간 전체에서 주기 수집한다. 순간 snapshot으로 peak를 주장하지 않는다. PPO rollout/update 구간별 시간도 가능하면 분리해 GPU 유휴 원인을 검사한다. GPU/호스트 모니터의 샘플 주기와 누락 여부를 함께 기록한다.

각 실행은 phase:P0, step:gpu-env-sweep, purpose:profiling 태그로 구분한다. 기존 supervisor의 종료·lease·자동평가 정책을 확인하여 학습 측정 구간과 평가/렌더링 구간이 섞이지 않게 한다. 실행별 자동 평가영상은 result에 보존하며, 프로파일링용 미수렴 정책임을 제목/설명에 명시한다.
