# P3-04 진행 및 인계

schema2 hold-last 두hop 학습을 course/deck에 허용했다. 기존schema1 계약은변경하지않았고mixed retention은schema2에서기각한다. terrain생성/hash/지지면목표여유검사와명시적fork/동일계약resume검증을적용했다.6개chain계약시험통과.

64env12update smoke(18,432step), 동일checkpoint부터2update resume(3,072step,iteration13~14),1024env60update profile(1,474,560step) 및각최종64환경평가/영상/200Hz/자원해제감사를통과했다. native평가가schema2의hold-last를자동상속하도록수정했고smoke에서확인했다. artifacts/p3-04-training-gates.json. 프로파일훈련wall56.79초. 초기profile의후반첫도약성공저하가보여서본결과에서회귀를반드시평가한다.

본학습을scripts/p3_04_train.py로시작했다. 실행session47669,로그artifacts/p3-04-training-batch.log. GPU0 course seed1, GPU1 deck seed1, GPU2 course seed2, GPU3 deck seed2. 각각1024env800update,부모는같은seed P240 checkpoint800. 별도warmup결과에서재개하지않았다. 실행시각실제GPU worker PID1992570/1992578/1992584/1992563확인. session종료/실제PID를확인하고관측timeout만으로재시작하지않는다.

아직학습결과가아니다. 본학습은자동native최종평가까지실행한다. 다음은완료상태/hash/학습step회계확인후protocol의course/deck/continuous회귀평가를수행하고부모대조를확보한다. GPU용도고정아니며작업종료후회수된다. 자동champion승격없음. P3계획연결은제한된기하학적경로이며동역학rollout검증/일반코스완료는미달이다.
