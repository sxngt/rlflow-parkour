# P2-19 행동 샘플링 진단

P2-18 최종 네checkpoint를 고정하고 동일64개 개발episode에서 mean과sampled 행동을 비교한다. 추가학습0step. 각모델 mean1회, sampled RNG20000/20001 두회,총12평가. mean은기존결과와episode사전동일성대조에사용한다. 이결과는훈련전체분포나여러학습seed를대체하지않는다.

정책/normalization은eval상태로고정하며관측·지형·초기calibration·성공기준·episode목록은동일하다. sampled는 PPO의update_distribution이계산한mean/std를사용한동일대각Gaussian분포다. 전용torch.Generator로매제어step전체env행에잡음을생성해reset난수와분리한다. 훈련의글로벌RNG시퀀스를그대로재생하는것은아니다. 종료된행도계속샘플링하여다른행의소비순서를유지한다.

mean은기존act_inference그대로이며이전P2-18의episode결과와대조한다. 차이가나면샘플링효과를해석하기전에실행차이를조사한다. sampled는2난수반복을별도보고하고 독립학습seed로세지않는다.

성공/유효비행/첫접촉/안정화와거리별성능,checkpoint의학습된std를기록한다. 200Hz진단과64개근접영상/result상세제목및phase:P2/step:p2-19-action-sampling/action:mean또는sampled 태그를남긴다. 새API는평가전용이며훈련코드는변경하지않는다. 결론에따라탐색방식을검토하되이진단만으로학습성능개선을주장하지않는다.
