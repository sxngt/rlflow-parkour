# P2-28 연속 지지면에서 분리 지지면으로의 전이

P2-27의 학습된4seed 최종1600checkpoint를 동결한다. 추가학습0step. seed2는retry1을사용한다. continuous/split에 동일15cm목표와64높이명령,총8평가512episode. 좋은seed만선별하지않는다.

지형은P226의검증된geometry/보정값/동일물리재질을재사용한다. continuous는발별24×12cm, split은출발/착지9×12cm에실제빈공간6cm. 포획면z−.5m,footradius2cm. 전신15cm갭도약으로주장하지않는다. 관측/보상/구동기/종료기준/mean행동은변경하지않는다. 기존P227혼합거리64episode를15cm고정군의대조군으로대신사용하지않고continuous64episode를새로평가한다.

GPU당seed1개,continuous→split순차,각240초제한. checkpoint/artifact사전감사후시작. 200Hz기록/64개렌더링/camera_side4/result상세제목/phase:P2/step:p2-28-support-transfer태그를남긴다. 완료후8감사·pairedscenario/checkpoint/calibration대조·최초접촉기하진단을실행한다.

유효비행전준비실패,거리미달,첫착지/유지실패를나눈다. 실패기록도분모에보존한다. 발판투영포함은접촉쌍이나지속지지보장이아니다. 새정책이continuous에서는도약하지만split에서실패하면실패시점/접촉순서/출발지지손실을다음학습설계근거로사용한다. 개발군전이진단이며최종시험/연속코스/실기검증이아니다.
