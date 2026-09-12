# P3-04 실제 코스 학습 결과

[동일조건18평가 비교](p3-04-comparison.md), [감사/거리별데이터](p3-04-comparison.json), [도약별진단](p3-04-failure-diagnosis.json). 4새학습×1024×24×800=78,643,200step. 2seed×course/deck고정예산비교,부모포함18평가×64episode. 모든실행정상종료,동일suite의scenario/support/chain/action계약일치,checkpoint/plan/영상hash검증. 64로봇camera4와phase:P3태그/result정리확인. smoke/profile계산은별도이다.

## 결과와 판정

코스 학습seed1/2의course첫도약은각64/64(부모51/64,0/64)로개선됐다. deck학습모델은course첫도약각0/64다. 하지만어떤조건도전체두도약완주를얻지못했다. 따라서연속파쿠르완주나champion승격근거가아니다.

course seed1의두번째도약은64개모두valid flight/출발영역/첫접촉정밀도를충족했지만비행거리7.70~9.01cm로요구12cm미달.49timeout/15failure,50개는거리조건이전의정밀안정화관측이있다. 거리미달을성공으로재분류하지않는다. seed2는첫도약후64개모두유효비행없이timeout. 서로다른실패를하나의원인으로단정하지않는다.

continuous단일거리0/5/10/15cm총성공은부모seed1/2=64/61,course학습=32/48,deck학습=59/1(각64episode). course seed1은5/15cm실패,seed2는0cm실패가집중됐다. 회귀가있으므로실제course첫도약개선만으로범용능력개선을주장할수없다. homogeneous후속학습과hold-last계약전환을포함한새fork의결과이고,첫도약개선의일반화는미검증이다.

이번공통deck평가는hold-last준비명령이다. 부모의과거default준비명령deck64/64와다르므로두결과를동일계약성능으로혼동하지않는다.

## 다음 경로

또다른보상가중치sweep을바로시작하지않는다. 실제course성공착지상태를후속도약학습의시작상태로활용하는실패/상태파이프라인을검토한다. 첫도약반복비용을줄이려면실제root/joint/velocity와센서이력을충분히기록하고물리적으로유효한재시작을검증해야한다. 현motion trace는완전한joint상태복구기록이아니므로현재자료만으로정확한reset을주장하지않는다. 기존능력유지를위한혼합평가/학습비율도명시해야한다. 우선두실패의근접영상검수와학습중hop별환경step분포를확인한다.

18평가session90541 exit0,보고/진단session85920 exit0. 추가근접영상session78456,로그artifacts/p3-04-closeup-batch.log. 동일64episode중1로봇만보이는추가화면이며기존64로봇최종영상을대체하지않는다. 새로운성능표본으로중복계수하지않는다. 추가영상의계측일치/시각검수는아직진행중이다.

학습중hop노출감사(p3-04-hop-exposure.json):course seed1/2의두번째hop은총step의39.08%/46.37%로각약768만/912만step을이미차지했다. 따라서두번째hop을거의경험하지못했다는설명은자료와맞지않는다. 성공착지상태파이프라인은재현/조건통제에유용할수있지만노출부족이원인이라는전제로다음학습을정당화하지않는다. 두번째성공은stochastic학습중각1회로희소했다. 고정mean평가0/64와분리한다.

추가근접영상2개session78456정상완료. 원래64로봇평가와전episode결과및모든motion-trace배열정확일치,chain감사통과(session74997). 각영상0.5초간격9장 contact sheet육안검수:seed1은후속동작후낮은자세,seed2는첫착지후다음비행없는자세유지로센서진단과일관된다. 단일표시로봇의표본frame관찰이지64환경전체frame검수는아니다. artifacts/p3-04-closeup-seed{1,2}-review.jpg. 64로봇원본과근접영상모두result보관. 이번실험단계의실행/비교/기본시각진단은완료했고코스완주는미달이다. 현시점진행중연구worker없음,다음실험은아직시작하지않았다.
