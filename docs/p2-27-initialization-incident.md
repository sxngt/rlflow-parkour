# P2-27 seed2 초기화 정체 관측

seed2 PID1522215가 Starting simulation 단계에서 학습 지표를 생성하지 않고 있다. 실제 프로세스는 살아 있으며 carb.tasking 스레드들의 CPU 누적 시간이 증가했다. 다른 세 seed는 같은 설정·환경수로 학습에 진입했다. 따라서 현재 증거는 seed2 시뮬레이터 초기화 경로의 정체를 가리키지만, 정확한 내부 원인은 미확정이다.

일반 gdb attach는 ptrace_scope=1 정책으로 거절됐고 sudo -n은 비밀번호가 필요했다. 보안 설정을 바꾸지 않았다. 스택 미확보 상태에서 deadlock·GPU 고장·PhysX 오류를 확정하지 않는다. 원본 로그와 /proc 스레드 관측은 artifacts/p2-27-seed2-*.json/txt에 보존한다.

현재 자원 스냅샷은 artifacts/p2-27-resource-snapshot.json이다. 각 프로세스가 exclusive GPU lease를 소유하므로 학습step이 없어도 자원 점유 시간을 계상한다. GPU 프로세스 존재 시간·할당 시간은 CUDA 연산 시간이나GPU utilization과 다르다. 종료 전에는 전체실험의 최종손실로 확정하지 않는다.

사전 실행 제한1800초를 유지한다. 같은PID와감독자상태를관측하고 실제종료전중복실행하지않는다. 종료시run.json과supervisor결과,프로세스소멸/GPU해제를대조한다. checkpoint가없는경우같은seed/설정의새attempt를최대1회검토하고원본실패를보존한다. 학습seed의성능결과교체로취급하지않으며기존시도의자원소비를별도계상한다. 재시도도정체하면동일무한재시도없이초기화경로의재현및설정진단으로전환한다.
