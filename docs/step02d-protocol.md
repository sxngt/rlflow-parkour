# P1 · Step 02d — 기존 보상의 추가 학습과 회귀

2026-09-11 학습 전 고정. 기존 A(v4)의 FL/RL seed0/1에서 800update 성공률이 각각 0/64와64/64로 갈렸다. 새 벌점의 적용 시점 비교가 진행을 해결하지 못하는 양상을 보여, 다음은 보상을 유지한 추가 계산 예산 실험이다.

A FL/RL seed0/1의 원래800update checkpoint를 optimizer·normalizer·RNG·adaptive LR과 함께 복구한다. 각1024환경×24step×추가800updates, 최종누적1600updates. 같은 seed를 유지하며 새 독립학습seed로 계산하지 않는다. episode경계재개로 미완료episode는 버려지므로 무중단1600update실행과 bitwise동일하다고 주장하지 않는다.

신규78,643,200steps, 기존4개800update run과 합친 실제총예산157,286,400steps. 800/1600 성능을 대응seed 내에서 비교한다. cumulative step을 두번 합산하지 않는다. 각GPU하나: FL0, RL0, FL1, RL1. 기존 source 원본은 보존하고 새attempt/run경로 및 parent_checkpoint SHA를 남긴다.

기존 보상·관측·성공기준·PPO·시나리오분포는 동일. learning iterations는 추가800으로지정. 연구태그는02d. 마지막checkpoint에서 동일64개개발episode deterministic평가와200Hz진단·16대MP4를 수행한다. 정상artifact완료 후 GPU회수.

주요질문: seed0의착지후안정화가추가예산으로개선되는가? seed1의기존성공은유지되는가? 무접촉·낙상·위치오차는어떻게변하는가? 추가예산으로성공해도800update에서더효율적인조건이라고주장하지않는다.

결과에따라미사용seed검증또는탐색/관측/커리큘럼을다음별도실험으로정한다. 재개를무한반복하지않는다. 최종시험군미사용, 자동champion승격없음.
