# P3-09 고정 정책의4도약 경로 확장

P308학습후같은checkpoint를학습하지않고4hop(목표60cm)/20패드course로확장한다. 현재지원하는지도graph최대4hop,발별15cm간격,6×12cm패드,9cm동일발gap. 같은64개개발초기조건/mapped_contact_v1/hold-last/4초hop예산. P308 mapped/strict학습seed1/2 총4모델을평가한다. 새학습0step. 길어진코스의성공/완료hop분포/첫실패계약/몸체비행거리조건을기록한다. 이는험지전체/고속/방향전환/경사지일반화주장이아니다.

실행전P308공통평가/보고서를검증한다. 각평가64로봇camera4영상/200Hz/result상세제목/phase:P3/step:p3-09-four-hop-course. 기하학적표면선택결과를geometric-plan.json에기록한다. 목표길이가늘어새collider도추가되므로3hop실험의단순시간연장만으로해석하지않는다. 결과에따라다음지형/계획/학습범위를결정한다.
