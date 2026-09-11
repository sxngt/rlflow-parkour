# P2-20 중간 체크포인트 사후 진단

최종 결과를 확인한 후 설계한 개발군 진단이다. seed0–3의 checkpoint800/1200을 평가하고 이미 완료된1600 결과와 비교한다. 추가 학습은 없다. 중간 모델을 최종 성능으로 대체하거나 승격하지 않는다.

모든 모델에 최종 출발 반경3cm와 동일한 거리0/5/10/15cm × 높이 명령16개, 총64개 episode를 적용한다. 기존 고정 지형·초기상태·PPO mean 행동·성공 판정·normalization 고정을 유지한다. 당시 훈련 조건의 재현은 아니다.

BoundedActorCritic의 checkpoint buffer std_floor/std_cap을 복원한다. 완료update800/1200/1600의 저장 cap은 각각0.35/0.20/0.10이어야 한다. 다음 학습 rollout의 cap과 혼동하지 않는다. raw std 대신 clamp된 실제 분포의 std를 기록한다. mean 평가 자체에는 샘플링 잡음을 추가하지 않는다.

주요 질문은 비행 거리 및 안정화가 중간에 획득되었다가 상실됐는지, 조사한 세 시점에서 계속 부족했는지다. 중간 두 체크포인트만으로 전체 학습에서 한 번도 습득하지 못했다고 단정하지 않는다. 커리큘럼·경과 step·cap이 함께 바뀌므로 개별 변경의 인과 효과는 분리하지 않는다.

각 GPU에 seed 하나를 배정하고800→1200 순서로 실행한다. 평가당 제한240초,200Hz진단,64개 렌더링/camera_side4/result 영상, 기존phase:P2/step:p2-20-bounded-exploration 및 purpose:checkpoint-diagnosis/checkpoint 태그를 보존한다. 완료 후8개 artifact감사, paired scenario/checkpoint hash/설정 일치 검증, 거리별 성공·최초접촉·안정화 보고서를 생성한다.
