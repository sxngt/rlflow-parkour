# P2-39 단일 목표 거리 범위의 고정 예산 비교

P2-38에서 continuous 회귀는 개선됐으나 혼합 seed2의10cm와 seed3의제자리 실패가 남았다. 단일 목표를0/15cm에서0/5/10/15cm로 확장하면 거리별 회귀와 연속 도약 성능이 개선되는지 검증한다. 아직 새 본학습은 시작하지 않았다.

## 고정 조건

대조는 P2-38 continuous의 seed0~3 최종800 checkpoint와 기존32평가 중 해당16평가를 명시적으로 재사용한다. 처치는 같은 P2-31 부모4개 checkpoint800에서 policy/critic/normalizer만 복사하고 새 optimizer/RNG로800 update,1024환경,rollout24step을 학습한다. 새 본학습78,643,200step, 재사용 대조78,643,200step. 파일럿은 별도이며 부모로 사용하지 않는다. 전체4seed를 포함하고 최종800을 사전에 고정한다.

단일 목표는 reset마다 네 값 중 균등 추출한다. rollout step별 거리 비중이 균등하다는 뜻은 아니다. chain512/single512 분할, 지지면chain deck/single continuous, chain15→30cm, PPO·보상·관측·탐험·episode·구동기·센서·physics 생성은 P2-38과 동일하다. 목표 이외의 변경이 필요한 경우 별도 기록하고 대조 재사용 가능성을 다시 판단한다.

## 착수 게이트

네 목표 계약·순서·중복·resume변경 거부, 실제환경별 지지면과 모든목표 포함 검사. 작은64환경12update에서 현재 정책 reset별 draw와 rollout 거리별 step을 검사한다. 기존2목표 경로와 네목표 경로 모두 회계 검사, 새목표 checkpoint 저장/2update재개,1024환경60update 프로파일링 후 본학습한다. 원본 실패 attempt는 보존한다.

## 평가

두도약deck64, 단일deck 및continuous 각각0/5/10/15cm×16, split15×64. 처치4모델16평가와 재사용대조16평가의 시나리오·모델·설정·학습예산을 검증한다. 각64환경 영상/camera_side4,200Hz 진단,result 상세거리 제목,phase:P2/step:p2-39-goal-coverage 태그. 개발군 비교이며 실패seed와 능력 회귀를 포함해 보고한다. 전체 코스나 실로봇 성공을 주장하지 않고 자동승격하지 않는다.
