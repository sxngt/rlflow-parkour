# P2-14: 실제 지지면 전이 파일럿

상태: 기하 manifest 및 독립 물리 낙하 probe 완료. 로봇 평가 장면 연결·정책 평가는 아직 수행하지 않았다.

## 질문과 고정 조건

P2-11 seed 0–3의 최종 1600-update checkpoint를 모두 고정한다. 추가 학습과 최상 seed 선택 없이, 무한 평지 / 발별 연속 지지면 / 발별 분리 지지면에서 같은 15cm 목표 전이의 실패를 비교한다. 이 실험은 학습군 밖 지형 전이 파일럿이며 최종 시험이나 전체 파쿠르 성능 검증이 아니다.

출발·착지 발판은 각 9cm × 12cm, 두께 10cm, 윗면 z=0이다. 각 발의 착지 목표는 출발 기준 +x 15cm이고 두 발판 사이의 빈 공간은 6cm다. 연속 지지면은 두 발판의 바깥 경계를 유지하면서 중간을 채운 24cm × 12cm다. 아래 포획 평면은 z=-0.5m다. 이는 발별 전이이며 로봇 몸체 전체가 15cm 갭을 건넌다는 뜻이 아니다.

발 이름과 좌표는 asset의 실제 순서 및 지지 평형에서 얻는다. 기하 생성기는 다른 발의 발판이 빈 공간을 덮는 겹침을 거부한다. 발 collider의 크기·접촉 offset을 조사하기 전에는 발판 전체를 유효한 접촉 영역이라고 주장하지 않는다.

## 평가 전 필수 물리 검증

1. 기존 평지의 300-step calibration 상태와 목표 좌표를 보존한다. calibration용 지지면을 제거·교체하는 시점과 physics 재초기화 방식을 명시한다. 교체 후 낡은 collider가 남지 않는지 확인한다.
2. 각 지지면 위·빈 공간 중앙에 독립 probe를 낙하시켜 접촉 높이를 측정한다. 빈 공간 probe가 z=0에서 멈추면 정책 평가를 시작하지 않는다. 단순 bounds 검사만으로 물리 검증을 대체하지 않는다.
3. 초기 네 발의 안정 지지, 인접 환경 간 충돌 격리, reset 후 같은 지형 유지, 아래 포획 평면 접촉이 성공으로 분류되지 않음을 확인한다.
4. checkpoint의 관측·행동·normalization 계약을 그대로 검사한다. 지형과 목표 분포의 평가 override는 원 학습 설정과 별도 manifest에 기록한다. 기존 restore 검사를 무조건 완화하지 않는다.

## 실행 및 보고

물리 검증 후 4개 checkpoint × 3개 조건 × 64개 episode를 평가한다. 조건 간 같은 높이 명령 seed를 사용한다. 원래 평가의 15cm 부분 집합도 참조하되 새 평가와 표본 수를 혼동하지 않는다. 학습 예산은 0 step이다. 시뮬레이터 초기화·검증 실패는 제어 실패와 분리한다.

완주, 유효 비행, 최초 접촉 위치/오차, 실제 비행 이동, 안정화, 비발 충돌, 지지면 이탈을 보고한다. 접촉력만으로 표면 ID를 확정하지 않고 접촉 위치·geometry 또는 지원되는 contact-pair 자료를 함께 확인한다. 기존 성공 정의와 지지면 내부 접촉 조건을 별도로 기록한다.

각 실행에 checkpoint hash, terrain manifest/hash, 원래 calibration, scenario seed, 200Hz 진단, phase:p2 및 step:p2-14-support 태그를 보존한다. 영상은 64개 렌더 활성화와 camera-side 4를 사용하고, result 제목에 평지/연속/분리 지지면과 seed를 명시한다. 실패 영상도 보존한다. 지형에서 실패하면 본 결과를 토대로 지형 커리큘럼을 다음 실험으로 사전 정의한다.

## 물리 검증 기록

`artifacts/p2-14-support-probe-a1-v4`에서 연속/분리 조건의 네 발 출발·중간·착지 위치에 반지름 1cm sphere 24개를 200Hz로 2초간 낙하시켰다. 24개 모두 기대 높이 ±5mm 및 최종 속도 0.02m/s 미만 조건을 통과했다. 분리 지지면의 중간 probe 4개는 중심 z=-0.49m에 도달했고, 나머지는 z=0.01m에 머물렀다. 중간 trace 저장은 20Hz이며 로봇의 200Hz 접촉 진단과 다르다. artifact hash 감사와 worker 종료·GPU 회수 확인을 통과했다.

A1 USD의 instance proxy 내부 collider를 조사했다. 네 발은 모두 Sphere이며 반지름 0.01999999955m, local transform identity, world 축 배율 [1,1,1]이다. local bounds는 ±2cm다. contact/rest offset은 명시된 USD 값이 없어 null로 기록했고, 이를 0이라고 가정하지 않는다. 발판 가장자리 여유의 초기 기하 기준으로 2cm를 사용할 수 있지만 실제 solver 접촉 범위는 별도 검증해야 한다.

범위 제한: 이는 새로 생성한 독립 장면의 검증이다. 로봇 calibration용 평면을 교체한 뒤 낡은 collider가 제거되는지, robot reset과 표면 접촉 판정이 올바른지는 아직 검증하지 않았다. 영상 없는 구현 probe이며 최종 정책 평가 영상이 아니다.

시도 이력: 첫 `support-probe-v1`은 물리 통과했지만 artifact hash 색인이 빠져 표준 감사 실패. `support-probe-a1-v1`은 instance proxy 누락으로 asset 조회 실패. v2는 물리·감사 통과했으나 invisible collision bounds가 비어 있었다. v3는 설치된 USD BBoxCache의 keyword 인자 호환 문제로 실패. v4에서 위치 인자 및 invisible bounds 조회를 수정해 위 결과를 얻었다. 이전 기록을 덮어쓰지 않았다.

## 로봇 장면 연결 및 초기 지지 검사

평지 calibration을 저장한 성공 평가의 root/joint/foot XY를 모든 조건에서 고정한다. 별도 evaluation_support 인자로 환경을 생성하고 asset의 실제 foot 순서를 검증한다. 물리 시작 전에 TerrainImporter의 원래 ground prim을 제거하고 같은 경로에 z=-0.5m GroundPlane을 다시 생성한다. 발판은 환경 복제 전에 env_0 아래 생성한다. 이후 기존 reset은 고정 calibration 상태로 돌아간다. 학습 checkpoint restore 계약은 변경하지 않았다. terrain.json과 scenario manifest에 평가 조건 및 calibration 원본 hash를 남긴다.

초기 구현은 ground의 상위 Xform만 이동했는데 `p2-14-robot-gap-v1`의 원시 발 높이 약 2cm와 정상 하중으로 숨은 지지를 발견했다. 이 장면의 정책 평가를 실행하지 않았으며 v1은 물리 검증 실패 기록으로 보존한다. prim 제거·재생성으로 수정한 `p2-14-robot-gap-v2`에서는 gap 중앙에 놓은 네 로봇 모두 약 0.08초에 실패하고 평균 0.07초의 발 무접촉을 기록했다. root 높이 변화는 약 2.9cm다. 종료가 빨랐으므로 포획 평면까지의 낙하를 관측한 것으로 주장하지 않는다.

`p2-14-split-stance-v2`에서는 출발 발판의 네 로봇 모두 4초 동안 실패 없이 지지했다. 무접촉 시간 0초, root 높이 변화 약 7.8mm다. zero action은 학습된 정책이 아니며 task timeout은 이 검사에서는 예상된 결과다. 두 실행 artifact 감사 통과. 연속 지지면 중앙의 대응 검사 `p2-14-robot-bridge-v2`는 후속 확인 대상이다.

정책 평가 CLI: --support-mode flat|continuous|split --support-calibration artifacts/p2-11-curriculum-seed0__final-evaluation/run.json. 모든 조건에서 +15cm 목표, 64개 높이 seed를 사용한다. --support-probe-offset .075는 zero baseline에서만 허용하는 구현 검사이고 실제 정책 비교에는 사용하지 않는다. 기존 성공 지표와 지지면 내부 접촉의 추가 분석은 분리해야 한다.

추가 확인: robot-bridge-v2도 네 대 모두4초 지지, 무접촉0초, 실패0으로 통과했고 artifact 감사·worker 종료·GPU 회수를 확인했다. 현재 모든 probe 종료, 정책평가 미시작.

## 추가 진단: 넓은 단일 발판 (정책 결과 확인 전 고정)

작은 지지면에서 전부 실패한 후, geometry 구현과 지지 영역 크기의 영향을 구분하기 위해 deck 조건을 추가한다. 이전 세 조건을 변경하지 않는다. 발판 크기는 1.4×1.2m, 두께10cm, 윗면z=0, 중심은 초기 네발 평균XY에서 +x7.5cm다. 같은 catch floor -.5m와 고정 calibration을 사용한다. 네 P2-11 checkpoint 각각 같은64높이seed/+15cm목표로 평가하고 학습은 하지 않는다. videos64/camera-side4, diagnostics200Hz, step:p2-14-support 및 terrain:deck. 추가진단으로 명시하고 원래세조건의 사전비교와 구분한다.
