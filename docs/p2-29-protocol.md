# P2-29 동결 출발 정책에서의 분리 지지면 추가학습

P2-28에서 seed0는 준비동작 지지 의존성, seed1/3은 비행거리 부족, seed2는 개발군 성공을 보였다. P2-27 네 최종정책 모두에서 두 추가학습 분기를 만들어 지형 변경의 효과를 비교한다. 좋은 seed만 선택하지 않는다.

| 분기 | 학습 지형 | 목표 | 추가 예산/seed |
|---|---|---|---|
| 대조 | continuous | 15cm 고정 | 1024env×24step×800update |
| 실험 | split | 15cm 고정 | 1024env×24step×800update |

4seed×2분기=8run, 신규157,286,400환경step. 같은 seed의 두 분기는 동일 P2-27 checkpoint에서 시작한다(seed2는retry1). 부모 정책·critic·normalizer를 복사하되 optimizer,학습률,RNG,커리큘럼진행은 새 분기의 명시된 설정으로 초기화한다. 부모 모델 파일의 모든 호환 tensor를 검사하고 부적합한 관측/행동/로봇 변경은 거절한다. 이것은 조건을 변경한 fork이며 동일조건 resume가 아니다. 부모의 과거학습step과 신규분기step을 따로 계상한다.

두 분기의 차이는 지형 계약과 태그뿐이다. 출발 반경3cm 고정, 기존관측·보상·PD·실패판정 유지. 새분기 탐색은update1–400 std상한.1,401–800 .05/floor.05로 동일하며 부모 정책 raw std와 실제분포 적용을 확인한다. 부모normalizer 상태를 계승한 후 학습 중 갱신한다. 이전trajectory를 replay하지 않고 현재정책으로 새 PPO rollout을 수집한다. 관측에지도경계를 추가하지 않는다.

학습/평가 명령은15cm로 고정한다. split에기존0–15cm 연속분포를 적용하지 않는다. 각uniform구간 전체가 단일발판의2cm투영여유안에 들어가야 하며,0과15cm가각각안전하더라도[0,.15]구간은거절한다. 초기자세의0cm위치도검사한다. 발판은기존검증된continuous24×12cm/split9×12cm/실제gap6cm/포획면−.5m를사용한다. 성공반경5cm전체의포함을의미하지않으므로평가의실제투영포함진단을유지한다.

주요평가: 8새모델 각각continuous/split에서같은15cm×64높이명령(16평가). 회귀평가: 각새모델continuous에서0/5/10/15cm×16 고정개발군(8평가),평가전용거리override를명시해훈련계약변경과구분한다. 부모기준은P2-27/P2-28의해당고정군과연결한다. 미완료·실패·낮은성공seed를제외하지않는다. 주된비교는같은부모seed의continuous추가학습대비split추가학습이며보편적개선/최초성/최종시험성능으로주장하지않는다.

실행전: fork호환성/계보/동일조건resume회귀,split목표구간기하검증,zero-action지지검사,각지형축소예산학습·평가·재개를검증한다. 본학습은GPU당run1개,seed0/2는continuous→split,seed1/3은split→continuous로순서를균형배치한다. 모든run의budget와원본을보존한다. 예산연장·seed교체·판정완화없이결과를기록한다.

각실행에phase:P2/step:p2-29-support-finetuning,checkpoint+부모hash,200Hz진단,64env/camera_side4영상,result상세제목을남긴다. 완주/비행거리/최초정밀/안정화/투영포함 및준비실패를보고한다. 실제갭전이의단일목표평가이며연속코스·Planner·실기성공을의미하지않는다. 구현/검증전에는본학습을시작하지않는다.
