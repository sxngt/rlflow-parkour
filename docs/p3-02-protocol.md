# P3-02 좁은 발판의 도약 준비 동작 비교

P3-01에서 두 번째 동작에 진입한51환경은 모두15step 준비 중 nonfoot collision로 종료했다. 기존 구현은 준비 중 관절offset을0(기준 자세)으로 되돌린다. 원인을 단정하지 않고 기존 hold-last 모드로 착지 시 마지막 관절 명령을 준비 중 유지하는 단일 변경을 평가한다.

P3-01과 동일 P240 seed1 checkpoint800,64개 개발 시나리오,course geometry,성공 판정,관측,mean정책,4초/hop을 사용한다. 변경은 chain_settle_mode default→hold-last만이다. 새 학습0step. 기존default결과를 대조로 재사용한다. 64로봇camera4영상,200Hz진단,phase:P3/step:p3-02-course-settle태그. 첫hop 일치,준비 중 명령 유지,물리 상태 비리셋을 검증한다. 개선해도 Planner완성이나 일반화를 주장하지 않는다.
