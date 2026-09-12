# P3-01 실행 결과 및 인계

고정 P240 seed1/800 모델의 실제 불연속 12패드 코스: 64 episode 중 완주0, 첫 도약 완료51, 첫 도약 미완료13. 기존 deck 두도약64/64를 이 지형에 그대로 일반화할 수 없다. 패드 크기도 변경됐으므로 지형 불연속성만의 인과 비교는 아니다. 새 학습 없음.

artifacts/p3-01-course-seed1: worker 정상 종료, GPU 프로세스/lease 해제 확인. 200Hz trace, episode/hop 경계, 물리 상태 보존, checkpoint/artifact hash는 scripts/audit_chained_evaluation.py의 check 통과. docs/p3-01-audit.json 및 p3-01-failure.json 참조. result/2026-09-12__A1__T1J-v5__seed-1__updates-000800__p3-01-course-seed1 에 상세 제목64로봇 영상과 manifest 등록. phase:P3/step:p3-01-course-integration 태그. 영상 육안 검수는 아직 하지 않았다.

기존 p2_32_failure_report.analyze는 두번째 준비 구간이 끝나기 전에 종료된 경우 prep_end<=end assertion으로 분석할 수 없었다. 원본 평가 실패가 아니라 과거 분석기의 적용 범위 제한이다. 새 집계는 조기 종료를 포함한 hop 원본 이벤트를 사용한다. 종료 조건은 원인 확정이 아니다.

다음 작업은 이 코스의 두번째 도약 준비 중 조기 종료와 실제 충돌 장면을 영상/센서로 확인하고, 사전 지도 기하학적 Planner 연결 및 실행기 전이의 필요 수정 범위를 결정하는 것이다. 보상 가중치 sweep으로 되돌아가지 않는다. 이 결과는 P3 완료도 Planner 구현 완료도 아니다.
