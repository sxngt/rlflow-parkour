# P2-41 고정 정책의 보상 성분 진단

학습이나보상변경없이P240seed1성공/seed3짧은비행실패의native두도약평가를다시실행한다. 기존800checkpoint/64scenario/mean행동/지지면/센서/종료규칙유지. --reward-components로그만추가한다. 각step50Hz grouped성분(dense비용묶음,비행,접촉,성공,실패,apex,첫접촉,travel)을기록하고합계와실제reward를atol2e-5/rtol2e-6으로대조한다. 원본200Hz진단과64로봇camera4영상/result제목·phase:P2/step:p2-41-reward-audit태그를보관한다.

계측전후기존평가의동일scenario/episode결과와motion trace를대조한다. 불일치시계측이무영향이라주장하지않고차이를조사한다. terminal step을포함하고완료뒤auto-reset rollout은합계에서제외한다. 보상항목합계는행동최적화의인과원인증명이아니다. 두모델진단을전체seed일반화로표현하지않는다. 진단이유효하면전seed로확장할지결정한다. 현재학습보상변경없음.
