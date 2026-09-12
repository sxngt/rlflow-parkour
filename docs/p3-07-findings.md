# P3-07 지도 접촉 코스 실행

고정P304 course seed1/800에서legacy strict2hop은0/64이고과거동일평가의전episode/전체200Hz trace와정확일치했다. mapped_contact_v1의2hop은27/64,3hop은0/64(첫hop64,두hop27,세hop0)이다. 새진행조건은별도과제계약이며legacy 12cm몸체공중이동성공을얻었다고주장하지않는다. [감사](p3-07-audit.json). 지정표면의첫접촉XY/최종발XY·Z/상향지지력은성공episode마다원본trace와별도검사했다.

새2hop은거리조건을단순삭제한것이아니라실제지도표면검사를추가했다. 두번째hop의기존정밀안정화사례중일부는표면검사에서기각돼27개만통과한다. 3hop의27진입중19개유효비행관측이있지만launch영역통과0,전체27failure다. 이제3hop코스학습으로확장한다. 이상결과는선택된1개개발모델이며일반화/고속파쿠르완료가아니다.

세영상모두64로봇camera4,result/상세제목/phase:P3/step:p3-07-mapped-course. 실행80402와감사42744정상종료. 새학습0step. mapped contact 단위시험(잘못된첫접촉/지지없음기각)과기존support geometry5시험통과. 지도3hop route선택/겹치지않는16패드확인. 원래엄격기준의감사조건은유지했고새기준에서만표면검사경로를명시적으로사용했다.
