# 시간 초과 후 잔존 worker 정리 수정

P2-27 초기화 정체에서 셸 래퍼는SIGTERM으로종료됐지만 같은프로세스그룹의Isaac worker는살아있었다. 기존코드는래퍼의wait결과만확인해SIGKILL로이어지지않았다.

scripts/process_group.py는start_new_session으로생성한작업의PGID와session이일치하는실행중프로세스를확인한다. 그룹전체에SIGTERM을보낸후최대10초기다리고,래퍼종료와무관하게남은그룹이있으면SIGKILL및최대5초회수확인을수행한다. zombies는실행자원을보유하지않는종료상태로구분한다. 별도세션으로탈출한임의프로세스까지추적하는일반적인컨테이너격리기능은아니다.

run_job의supervisor결과에process_cleanup(전송신호/잔존PID)을추가했다. GPU잔존과프로세스잔존이둘다없을때resource_released=true이며,자동평가/영상수집및정상반환도이상태를요구한다. 원래FAILED/timeout상태를성공으로바꾸지않는다.

검증: 실제별도프로세스단위3테스트(래퍼먼저종료+SIGTERM무시자식/무관세션보존,정상SIGTERM종료,자연종료무신호). 전체61unit통과 artifacts/process-cleanup-tests.log. 실제run_job에synthetic_cleanup_test worker를연결한timeout통합검증에서SIGTERM/SIGKILL·remaining_processes=[]·resource_released=true·workerFAILED를확인했다. artifacts/cleanup-timeout-regression.supervisor.json. 약13.24초는2초예산+10초회수유예+상태확인비용이다. 합성worker는GPU계산을하지않으므로Isaac GPU해제자체의재현시험으로과장하지않는다.

현재실행중인seed2 retry의기존supervisor를교체하거나재시작하지않았다. 수정은이후시작되는실행기에적용된다. 현재학습은계속추적한다.
