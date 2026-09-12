# P2-31 이전 능력을 가진 출발 정책에서 직접 혼합 학습

P230 mixed seed1/2는0cm에서32회모두시간제한으로끝났고,200Hz기록상네발공중구간이있어도최대몸체상승이각2.953/2.496cm로유효도약3cm기준에미달했다. 기준을완화하지않는다. P229에서잃은능력을나중에복구하는대신,continuous0cm평가를통과했던P227네부모로돌아가직접split0/15cm혼합을학습한다. P227의split0cm능력은아직확인하지않았으므로학습전에동일split0/15×32평가를기록한다.

주비교는동일P227부모에서출발한P229split15cm전용800update 대조군과P231split0/15혼합800update다. 전용군은기존정책/평가를재사용한다. 부모4seed전부포함,seed2는P227retry1정책이다. 새4run×1024env×24step×800update=78,643,200step. 각조건예산은4run씩동일하다. P230은추가학습량과출발checkpoint가다르므로주된동일예산비교에섞지않는다.

P231설정은P230mixed와같으며새실험태그만변경한다. policy/critic/normalizer계승,새optimizer/LR/RNG/update0,탐색cap.1(1–400)/.05(401–800),reset별동일확률0/15cm,기존보상·관측·PD·3cm출발반경·유효도약3cm기준유지. split의갭중간목표는거절한다. 기존fixed제어군과의차이는학습목표분포와평가명세/태그다. 코드변경중기존연속목표sampler의RNG소비와출력동일성은테스트했으며,새목표계상은진단전용이다. 코드버전차이가있다는점은보고한다.

평가:split0/15×32 native,continuous0/5/10/15×16회귀,split15×64유지각모델4개. 기준P229정책의split혼합은P230parent평가를재사용하고나머지는동일시나리오의P229평가를재사용한다. P227원본의split혼합4개는출발상태진단이며정답지형/정답마찰정보를policy에추가하지않는다.

새학습전각부모hash/완료감사와fork허용변경을검사한다. seed별GPU한장에부모평가→새학습→자동native평가를실행한다. 실패시해당seed의다음단계를진행하지않고기록한다. checkpoint/200Hztrace/상세제목result영상64env camera4/phase:P2 step:p2-31-direct-retention태그보존. 모든seed및거리별손실을함께보고하며예산연장/불리한seed삭제/판정완화를하지않는다. 개선여부는가설이며연속점프·Planner완료를뜻하지않는다.
