# 연구 phase·실험 태그 계약

태그는 연구 작업의 분류이며 phase 완료 또는 성능 달성을 의미하지 않는다. 하나의 실행에 여러 태그를 부여한다. 태그 ID는 고정하고 한국어 표시 이름은 `configs/research-tags.json`에서 관리한다.

| 구분 | 예시 | 의미 |
|---|---|---|
| phase | phase:P1 | 계획서 P0–P7 분류 |
| step | step:01-hopping-diagnosis | 구체적인 실험 단계 |
| task | task:sequential-foothold | 제어 과제 |
| purpose | purpose:diagnosis | 본 진단, 기준선, 계측 파일럿 구분 |

현재 진단은 P2 동적 도약에 앞선 기준선 점검이므로 P1이다. 순서 01–07과 계획서 phase P0–P7은 서로 다른 축이다. 단일 도약은 step:03-single-jump / phase:P2, Planner 비교는 step:05-planner / phase:P3로 구성한다.

## 기록과 상속

새 학습은 config의 `research_tags` 배열에 기록한다. evaluate는 반복 가능한 `--research-tag` 인자로 지정할 수 있다. 실행 시작 시 run.json 및 config.json에 저장하고 영상 archive manifest에도 복사한다.

```json
{"research_tags":["phase:P1","step:01-hopping-diagnosis","task:sequential-foothold","purpose:diagnosis"]}
```

분류 우선순위는 registry의 run_overrides → 실행에 명시된 태그 → task_defaults → 미분류다. 과거 실행의 artifact·checkpoint hash를 바꾸지 않도록 기존 파일은 수정하지 않고 API가 버전 관리된 registry로 주석을 덧붙인다. tag_source에서 명시/파생/수동 분류 출처를 확인할 수 있다.

P0 모델 검증 4건은 registry에서 명시했다. 최초 계측 확인용 seed 0 실행은 purpose:instrumentation-pilot로 구분하고, 동일 v2 프로토콜의 seed 0–3과 zero 대조군 5건만 purpose:diagnosis로 분류한다.

실행 파일은 해당 run의 태그를, result 파일은 평가 manifest의 태그를 상속한다. docs/configs는 공용 문서여서 실행 태그로 숨기지 않는다. SQL에 물리 step별 센서 데이터를 넣지 않고 실행 아래 NPZ 파일로 보존한다.

## 웹에서 찾기

상단의 Phase, 실험 단계, 과제, 목적을 조합하면 모든 선택 태그를 만족하는 실행·영상·파일이 표시된다. 이름 검색은 해당 필터 결과 안에서 적용한다. 현재 진단만 보려면 **P1 → 01·hopping 진단 → 목적: 동작 진단**을 선택한다. 실행 상세의 지표·평가 탭에 200Hz 진단 요약과 episode별 표가 표시된다.

API도 같은 AND 조건을 지원한다.

- `GET /api/tags`: ID·표시 이름·실행 개수
- `GET /api/runs?tag=phase:P1&tag=step:01-hopping-diagnosis`
- `GET /api/videos?tag=purpose:diagnosis`
- `GET /api/files?path=artifacts&tag=purpose:diagnosis`
- `GET /api/runs/{id}/diagnostics`

향후 새 단계는 registry와 실험 config에 태그를 추가한다. 웹에서 임의 shell 실행이나 공인 쓰기 API를 제공하지 않는다.
