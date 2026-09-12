# P3-05 실제 착지 상태 수집

추가학습없이고정P3-04 course seed1 checkpoint800의64episode를계측한다. 성공한첫도약의전환경계에서root13D(위치/자세/속도),joint위치/속도,명령/이전명령,접촉history/이벤트상태,새목표/관측,시간과환경원점을저장한다. 파일hash와scenarioID를연결한다. 완전한시뮬레이터checkpoint나reset동등성을주장하지않는다. solver warm-start/숨겨진구동기상태는포함하지않는다.

기존동일평가와전episode 및200Hz trace일치로읽기계측이행동을바꾸지않았는지검증한다. 64로봇camera4영상/result/phase:P3/step:p3-05-transition-states. 새학습0step. 이후이기록을재현시나리오에쓸수있는지는실제복구동작과물리유효성검증후결정한다.
