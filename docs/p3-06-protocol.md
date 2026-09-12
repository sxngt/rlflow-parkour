# P3-06 저장 착지 상태의 복원 검증

P305의64개성공첫착지상태를같은checkpoint/terrain/관절/접촉body순서의별도환경에적용한다. rootpose/velocity,jointposition/velocity,관절명령/이전명령,접촉history,도약clock/원점/새목표를복원한다. solver내부warmstart와숨겨진구동기상태동등성은보장하지않는다. 새학습0step. 복원직후관측오차,원본첫후속control-step/root/발위치와접촉력차이,후속성공/실패기준을측정한다. 허용오차를사후통과기준으로조정하지않고측정값을보고한다. 학습reset편입결정은별도이다.

성공은복원상태에서남은hop에만해당한다. 전체코스완주로집계하지않고report.evaluation_scope/restored_prior_hops/course_successes:null,영상상세제목에표시한다. 기존globalepisodeclock이유지되므로기존전체course감사기를그대로적용하지않고source_step과trace offset을대응한다. phase:P3/step:p3-06-transition-restore.64로봇camera4영상/result.
