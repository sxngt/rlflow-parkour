# parkour 모니터링 웹 — 2026-09-10

현재 서버의 `artifacts/`, `result/`, `docs/`, `configs/`를 탐색하는 조회용 웹이다. 학습 worker는 변경하지 않으며 별도 Python 3.11 환경에서 실행한다.

- 서버 브라우저: http://127.0.0.1:8710
- Tailscale 연결 기기: http://100.104.103.77:8710
- 일반 공인 인터페이스에는 바인딩하지 않는다. Tailscale Serve 설정 없이 해당 사설 인터페이스에 직접 바인딩한다.
- 브라우저 탭이 닫혀도 수집을 계속한다. user systemd 서비스와 linger를 활성화했다.

## 제공 화면

1. 전체 현황: GPU 4장의 사용률·VRAM·온도·전력·SM clock·compute PID, CPU/RAM/디스크 여유, 최근 실행, 수집 이후 GPU 이력.
2. 실행 기록: 작업·상태·이름 필터, 학습 update/환경 step, 접촉 수·종료 episode 성공 비율·PPO loss·update 시간, 고정 평가 episode 결과, 설정/계보, 로그, 파일.
3. 실험 비교: 최대 4개 학습 run의 곡선, 표준 이름으로 연결된 최종 평가. 학습 중 성공 비율과 고정 평가 성공률을 별도로 표시한다.
4. 영상 라이브러리: 제목·seed·update·완주 결과·미리보기, 실제 학습/최종 평가 선택, 다운로드.
5. 영상 분석: 표시 로봇 선택, simulator 시간 이동, 몸체·발의 월드 높이와 접촉 진행 단계. 기존 병렬 기록에 없는 접촉력·충격·행동은 미수집 표시. 과거 단일 영상의 단계 정보도 없으면 미수집이다.
6. 파일 탐색: 연구 폴더 이동, 텍스트 첫 256 KB 미리보기, 이미지·MP4 재생, 원본 다운로드.

실시간은 지표·상태의 약 2초 갱신을 뜻한다. 완료된 원본 MP4를 재생하며, 실시간 카메라 방송은 포함하지 않는다. 학습 실행/취소/승격 기능은 이번 조회용 버전에 없다.

## 구성

- React 19 + TypeScript + Vite, Apache ECharts. 정확한 버전은 `web/package-lock.json`.
- FastAPI, Uvicorn, psycopg, psutil. 정확한 버전은 `monitor/requirements.lock`.
- 이 서버에 설치된 PostgreSQL 12.22 바이너리로 **별도 로컬 클러스터** 사용. `.monitor/postgres`, Unix socket만 사용하며 호스트의 기존 DB 설정은 변경하지 않는다.
- 별도 수집기가 파일 변경 시각·크기를 검사하고 JSONL을 byte cursor부터 읽는다. 미완성 마지막 줄은 다음 수집까지 보류한다. inode 교체·관측된 truncation을 처리한다. append-only 로그 계약이며 임의의 과거 행 수정은 지원하지 않는다.
- PostgreSQL `records`: run/영상 manifest/수집 상태. `metrics`: PPO update 단위 데이터. `cursors`: 증분 읽기 위치. `telemetry`: 운영 시계열(7일 보존).
- 매번 원본 재귀 스캔이나 checkpoint 역직렬화를 하지 않는다. MP4·checkpoint는 원본 파일로 제공한다.
- SSE는 변경 재조회 신호이며 재접속 후 HTTP로 최신 상태를 받는다. 브라우저는 10초 재조회도 수행한다. 15초 이상 수집이 끊기면 지연을 표시한다.
- 잘못된 JSON은 마지막 정상 색인을 유지하고 경고를 표시한다. 새 파일/지표/영상은 자동 편입된다.

## 설치·재실행

이 호스트의 Python 3.11, Node 22, PostgreSQL 12 바이너리 경로 기준이다.

```bash
python3.11 -m venv .monitor-venv
.monitor-venv/bin/pip install -r monitor/requirements.lock
cd web
npm ci
npm run build
cd ..
python3 scripts/setup_monitor_database.py
python3 scripts/install_monitor_services.py --private-host 100.104.103.77
loginctl enable-linger sxngt
```

다른 호스트에서는 사설 IP를 해당 기기 주소로 바꾸거나 `--private-host`를 생략해 loopback만 사용한다. 다른 PostgreSQL 버전은 setup/install 스크립트의 바이너리 경로를 맞춘다. 서비스의 루트 경로는 설치 시 현재 저장소 경로로 생성한다.

```bash
systemctl --user status parkour-monitor-db parkour-monitor-collector parkour-monitor-web
journalctl --user -u parkour-monitor-collector -n 50
journalctl --user -u parkour-monitor-web -n 50
systemctl --user restart parkour-monitor-collector parkour-monitor-web
```

웹 변경 후 `web`에서 `npm run build`. Python 변경 또는 자산 mount 구조 변경 후 web 서비스 재시작. DB 재시작으로 의존 서비스가 내려갔다면 위 collector/web 재시작 명령을 함께 실행한다. 종료는 `systemctl --user stop parkour-monitor-web parkour-monitor-collector parkour-monitor-db`.

## 검증

- 최초 연결: 실제 실행 45건, 평가 영상 묶음 14개(실제 학습 영상 1개 추가).
- TypeScript 검사와 production build 통과.
- 별도 임시 PostgreSQL schema에서 테스트 4개: 미완성 JSONL→추가 기록→수집기 재시작→파일 교체, 손상 메타데이터 처리, HTTP byte-range·경로 제한·증분 cursor, 병렬 replay 환경 선택.
- 실제 영상 14묶음 및 추가 학습 MP4의 byte-range 응답, replay JSON 응답 확인.
- loopback/Tailscale 인터페이스에서 HTTP 200, SSE 이벤트 수신, 수집 health 확인.
- 수집기·웹 서비스 재시작 전후 학습 지표 5,231행 유지: 중복 생성 없음.
- 브라우저에서 직접 클릭·레이아웃을 검수하는 테스트는 이번 검증에 포함하지 않았다.

```bash
.monitor-venv/bin/python -m unittest monitor.test_monitor -v
```

원본은 조회만 하며 `artifacts/`와 `result/`를 자동 삭제하지 않는다. DB 색인은 다시 만들 수 있지만 모니터링 시계열은 재구축되지 않는다. `.monitor/`, `.monitor-venv/`, `web/node_modules/`, `web/dist/`는 Git에서 제외한다. 서비스 로그는 user journal에 기록한다.

구현 참고: [Starlette 파일 응답·Range](https://starlette.dev/responses/), [Vite 환경 요구](https://vite.dev/guide/), [psycopg 트랜잭션](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).
