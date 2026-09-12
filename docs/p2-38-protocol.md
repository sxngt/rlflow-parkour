# P2-38: 단일 과제 지지면 혼합의 고정 예산 비교

질문: P2-36과 같은 목표 과제 비율을 유지하면서 단일 과제 환경의 지지면을 continuous로 바꾸면 기존 지형 성능 유지가 개선되는가? 연속 도약은 유지되는가?

## 비교와 예산

- 부모는 P2-31 seed0~3 checkpoint800 전체. 각 조건은 같은 부모에서 policy/critic/normalizer만 복사하고 optimizer/RNG/update를 새로 시작한다.
- A: P2-36의 50:50 목표 과제 배치, 모두deck. B: 같은 배치에서 앞 절반chain환경은deck, 뒤 절반single환경만continuous.
- 단일 목표0/15cm동일확률reset, 연속15→30cm, 같은PPO·관측·보상·탐험 스케줄·4/8초종료 계약을 유지한다. 태스크ID나지형정답관측을추가하지않는다.
- 각조건×4seed×800update×1024env×24step. 총신규157,286,400step. 이전P236은참고결과이며이번대조예산으로재사용하지않는다. 파일럿·평가예산별도.
- 4 GPU에 seed별한작업. 짝수seed A→B, 홀수B→A로시작순서를분산한다. 총step동일이지wall-clock동일을의미하지않는다.

## 물리 생성 방식과 대조군이 필요한 이유

현재task.py는env0지형을모든환경에복제하며replicate_physics=True다. 설치된IsaacLab의InteractiveScene문서는서로다른asset의환경에서는replicate_physics=False를요구한다. 두조건모두이를사용하고로봇을복제한후각환경의지형을독립생성한다. env0상속으로뒤환경에deck이남지않도록copy_from_source=True를사용한다. 기존P236과물리생성경로가달라지므로새A대조를함께실행한다.

각환경지형은기존build_support_layout의동일Cuboid와재질을사용한다. 단일과제continuous는기존24×12cm 발별4지지면,deck은140×120cm공유발판이다. 지형모양외의보정·높이·마찰·반발계수·발판밖catch floor는유지한다. 지형을mesh로치환하거나실행중크기를바꾸지않는다.

## 본학습 전 게이트

1. 엄격한버전계약과환경ID별geometry분할검증. fork/resume에서지형배치변경을묵인하지않는다.
2. 양조건작은환경실행에서모든Supports의개수·경계·collision활성·재질,환경0/경계전후/마지막로봇의상태와접촉을확인한다. 단일환경에잔여deck이없어야한다.
3. replicate_physics=False GPU환경의collision filter를명시적으로설정하고환경간충돌분리도검증한다.
4. 기존고정모델을새생성경로로평가하여수치차이/성공률변화를기록한다. 동일성을확인하지않고기존코드와bitwise동일하다고주장하지않는다.
5. 64환경smoke/저장·재개/기존명시적평가override와1024환경60update프로파일링. 단일·연속과제step합계와실제두번째노출확인. init비용도포함해CPU/RAM/VRAM을측정한다.

게이트실패시원본실패artifact를보존하고원인해결후새attempt로실행한다. 파일럿모델을본학습부모로쓰지않는다. 이문서작성시본학습은시작하지않았다.

## 최종 평가

두도약deck64,단일deck0/5/10/15각16,단일continuous동일거리각16,split15×64. 양조건4seed전부평가하고같은시나리오/모델계보/총예산을검증한다. 모두200Hz진단,64render/camera4,result상세제목,phase:P2/step:p2-38-support-mixture태그를남긴다. 성공과퇴화seed를모두보고하고최신checkpoint자동승격은하지않는다.
