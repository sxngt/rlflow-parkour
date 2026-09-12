# P3-08 실제3도약 코스 학습

P307의mapped 2hop27/64,3hop0/64에서3hop코스전체학습으로진행한다. 두조건은mapped_contact_v1 vs strict_travel_v1진행/성공계약이다. 같은16패드course/3hop/12초상한/hold-last/보상계수/관측/PPO를사용한다. 성공보상이각계약의성공에연결되는차이는명시적으로포함된다. 엄격몸체비행거리결과와지도접촉결과를혼합해보고하지않는다.

각seed1/2는같은P304 course seed의checkpoint800에서새fork한다. optimizer/RNG새시작,policy/critic/normalizer복사. 각조건1024env×24×800update=19,660,800step,4run총78,643,200step. 64env12update smoke와2update resume를선행하고본학습부모로사용하지않는다. GPU4장에독립배치,예산종료후새명세없이무한연장하지않는다.

평가:모든후보/부모를같은mapped3hop64episode와legacy strict2hop64episode,continuous단일0/5/10/15cm64episode로비교한다. 기존P304평가는계약이같을때만대조로재사용한다. 전체3hop완주/각hop첫접촉·지지·비행·launch/정규화gap/진행거리/기존능력회귀를보고한다. 고정개발조건결과이며최종시험일반화아니다. 64로봇camera4,result상세제목/200Hz/계보/phase:P3/step:p3-08-three-hop-training. 자동승격없음.
