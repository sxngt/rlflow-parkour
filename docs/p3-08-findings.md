# P3-08 학습 및 공통 평가 결과

[비교표](p3-08-comparison.md), [검증데이터](p3-08-comparison.json). 4개800update학습과18개동일계약평가를완료했다. 새학습78,643,200step,smoke/resume별도. 초기pipeline은standalone모듈경로오류로학습후감사에서멈췄고src경로를수정해평가부터재개했다. 학습을중복하지않았다. 원본로그와재개로그보존.

mapped3조건에서부모seed1/2는0/0,지도접촉학습후64/64,엄격비행학습후0/61(각64episode). legacy strict2조건은지도접촉학습seed1/2=0/64,엄격학습=0/64다. 지도접촉학습seed2는새지도표면기준과기존엄격2hop기준을모두충족했다. 모든기준을같은성공으로혼합하지않는다.

continuous0/5/10/15cm합계는부모32/48,지도접촉학습48/40,엄격학습16/58이다. 부모대비회귀가남은조건이있으므로champion승격은하지않는다. 좁은발판의고정3hop개발코스성과이며고속/경사지/방향전환/최종시험일반화가아니다.

각suite의scenario/support/chain/action동일성,모델/계획/영상hash,계보,64로봇camera4,200Hz/접촉표면검사통과. 재개pipeline session60532 exit0. 최종감사에서npz필드를반복해압축해제하는병목을찾아모든필드를1회읽는방식으로개선했다. 당시기존감사프로세스는중단명령전정상완료되어실제중단/재실행은없었다. 검사조건은유지했고이후평가에서적용한다.

현재P309의4hop60cm/20패드경로평가로진행했다. active session41010,로그artifacts/p3-09-evaluation-batch.log. 사용자요청에따라단계보고로전체진행을멈추지않고코스길이확장과이후지형변화로이어간다. 이번영상은result/의p3-08-eval-*폴더에보존한다. 태그:학습step:p3-08-three-hop-training,명시적비교평가step:p3-08-course-training,공통phase:P3. 이름차이를숨기지않으며두태그를함께찾아야이단계전체를조회할수있다.
