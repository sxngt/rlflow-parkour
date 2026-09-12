# P2-30 제자리 도약 능력 유지 비교

P2-29 split 학습 네 정책을 모두 출발점으로 사용한다. seed0만 선별하지 않는다. 각 부모는 split15cm 및 continuous15cm에서64/64 성공했지만 seed1~3은continuous0cm에서1/0/0 성공으로 회귀했다.

두 분기는 동일 split 지형에서 800update × 1024env × 24step을 새로 수집한다. 대조군은15cm전용, 실험군은episode reset마다0cm 또는15cm를동일확률로선택한다. 총4seed×2조건=157,286,400신규step. 이는reset별50:50이며step/완료episode비율이 정확히50:50이라는 뜻이 아니다. 목표별 배정과 관측량을 기록해 차이를 보고한다. 갭 중간5/10cm를split학습에서샘플링하지 않는다.

부모: artifacts/p2-29-split-seedS/checkpoint-000800.pt. policy/critic/normalizer를계승하고optimizer/LR/RNG/update를새로시작하는명시적fork다. 두조건모두탐색cap.1(1–400)/.05(401–800),기존보상·관측·3cm출발반경·종료조건·재질·로봇유지. seed0/2는대조→혼합,seed1/3은혼합→대조로순서를균형배치한다. 보상변경·예산연장·불리한seed제외는하지않는다.

기본비교평가: 모델8개각split에서0/15cm×32동일높이명령(8평가),continuous에서기존0/5/10/15cm×16(8평가). 부모8평가도새고정split혼합군/기존continuous회귀군으로맞추며이미동일시나리오인결과만재사용한다. 추가15cm×64split평가8개로P22915cm능력유지확인. 모든평가는전체64episode를완료하고학습seed별로보고한다. 단일성공률로기존능력손실을가리지않는다.

0cm는departure,15cm는landing발판이예상지지면이다. 지지면진단은목표와명목발위치로해당표면을선택하고2cm발구투영여유를검증한다. 평가목표의보간은허용하지않는다. 동일goal명령이관측에들어가며정답마찰/지도정보를추가하지않는다.

실행 전: 이산샘플링의지정값외출력없음/RNG재현성/균등확률/연속범위와동시지정거절,전체목표기하가용성,split부모fork허용변경경계,기존resume규약유지,0cm지지면진단,축소예산양조건학습/평가/재개를검증한다. 검증후본학습. 모든checkpoint·평가·200Hz진단·result영상·phase:P2/step:p2-30-capability-retention태그를보존한다. 영상은64개렌더링/camera_side4.

이번비교는기억유지의한조건시험이다. continuous5/10cm회귀도검사하지만split의그목표는물리적으로가용하지않다. 연속점프·경로계획성공을의미하지않으며P230목표회복후에연속실행계약으로진행한다.
