# P2-07 · 3cm 출발 조건 재평가

학습을 추가하지 않고 P2-07 네 최종1600-update checkpoint를 그대로 평가한다. 출발 반경만6→3cm로 변경하고 같은64개 개발 시나리오·종료 기준·영상·200Hz 진단을 사용한다. 보고서의 궤적 부분집합을 실제 엄격 종료조건 실행과 대조한다.

`evaluate.py --launch-radius .03`은 고정 모델 평가에서만 허용한다. DirectedJumpEnv와 checkpoint를 요구하며 유한한 양수이고 원래 설정보다 크지 않아야 한다. 기존 restore는 원래 계약 그대로 검사한 뒤, 평가 환경의 출발 반경만 변경한다. checkpoint_training_config와 evaluation_override 및 적용 config.json을 기록한다. 학습 resume 계약 검사는 변경하지 않는다.

각 모델의 학습 GPU와 같은 GPU에서64개 평가·16로봇 영상. 실행 이름 `p2-07-{zero,short}-seed{0,1}__strict-evaluation`. 시간 제한600초. 태그 phase:P2, step:p2-07-launch-region, condition:launch-3cm-evaluation. 새 환경 step은 평가에만 사용하며 학습 예산은0이다.

성공률·출발 영역 위반·유효 비행·거리별 조건을 비교하고 원본과 좌표를 대조한다. 출발 영역 위반은 비행 확인 직후 즉시 종료되므로 기록의 stage 전환 이전 종료도 고려한다. 성공 사례만 선택하지 않는다. 정밀한5cm 비행 전이의 두 seed 재현성을 주장하지 않으며 champion 자동 승격은 없다.
