# P3-05 성공 착지 상태 수집 검증

기존관측검토:targets는몸체기준좌표,관절/속도/접촉과도약phase/목표높이/도약별준비clock을입력한다. ChainedDirectedJumpEnv는물리상태를리셋하지않고목표와도약별clock/bookkeeping을갱신한다. 이번검토에서목표가월드절대좌표로잘못입력되거나episode전역clock만쓰는문제는확인되지않았다. 이것이관측의충분성까지입증하지는않는다.

고정P304 course seed1/800에서64개성공첫착지전이의root13D,관절위치/속도,actions/previous_actions,contact_on/history,환경원점,clock,새목표/관측,launch origin,required apex를수집했다. scene상태변경없이전이경계에서CPU사본만생성했다. 원본과전episode결과및모든200Hz motion-trace배열정확일치. snapshots의rootXY/Z/Vz/명령이전이경계trace와일치,목표는chain-event와일치,quaternion norm/finite/차원검사통과. joint name순서와접촉body이름을저장했다. [감사](p3-05-audit.json),실행scripts/p3_05_audit.py.

실행artifacts/p3-05-transition-states-seed1의transition-states.json/.npz는run artifact hash에등록됐다. 64로봇camera4영상/result복사hash검증. phase:P3/step:p3-05-transition-states. 실행session56630 exit0,감사session38071 exit0. 새학습0step. 실행중연구worker없음,디스크523GB여유확인.

이것은완전한시뮬레이터checkpoint가아니다. solver warm-start,숨겨진구동기상태및전체정책이력복원등은보장하지않는다. 접촉history를읽었다고물리접촉solver상태를복구했다고해석하면안된다. 다음은같은모델로저장된실제착지상태를별도env에적용해첫관측/첫control-step/이후궤적오차를측정하고,침투/비정상초기충격을검사하는복구검증이다. 실패하면그상태를그대로학습reset분포에편입하지않는다. 실제코스완주0/64라는기존결론은변경없다.
