# parkour 모니터링 웹 — 2026-09-10

현재 서버의 `artifacts/`, `result/`, `docs/`, `configs/`를 탐색하는 조회용 웹이다. 학습 worker는 변경하지 않으며 별도 Python 3.11 환경에서 실행한다.

- 서버 브라우저: http://127.0.0.1:18710
- Tailscale 연결 기기: http://<tailnet-host>:18710
- 사용자 요청과 연구실 규정에 따라 0.0.0.0:18710에 바인딩한다. 공인 접속 주소는 http://<lab-server>:18710 이다. 현재는 로그인 없는 조회용 웹이며 연구 파일과 영상 다운로드를 제공한다.
- 브라우저 탭이 닫혀도 수집을 계속한다. user systemd 서비스와 linger를 활성화했다.

## 제공 화면

1. 전체 현황: GPU 4장의 사용률·VRAM·온도·전력·SM clock·compute PID, CPU/RAM/디스크 여유, 최근 실행, 수집 이후 GPU 이력.
2. 실행 기록: 작업·상태·이름 필터, 학습 update/환경 step, 접촉 수·종료 episode 성공 비율·PPO loss·update 시간, 고정 평가 episode 결과, 설정/계보, 로그, 파일.
3. 실험 비교: 최대 4개 학습 run의 곡선, 실제 checkpoint 출처로 연결된 평가. 학습 중 성공 비율과 고정 평가 성공률을 별도로 표시한다.
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
python3 scripts/install_monitor_services.py --public --port 18710
loginctl enable-linger sxngt
```

공인 배포는 `--public`, 사설 인터페이스 추가는 `--private-host <IP>`, 둘 다 생략하면 loopback만 사용한다. 웹 포트는 10000–19999만 허용하며 개발 서버도 18711을 사용한다. 다른 PostgreSQL 버전은 setup/install 스크립트의 바이너리 경로를 맞춘다. 서비스의 루트 경로는 설치 시 현재 저장소 경로로 생성한다.

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
- 별도 임시 PostgreSQL schema에서 테스트 5개: 미완성 JSONL→추가 기록→수집기 재시작→파일 교체, 손상 메타데이터 처리, HTTP byte-range·경로 제한·증분 cursor, 병렬 replay 환경 선택, 이름과 무관한 checkpoint 계보 연결.
- 실제 영상 14묶음 및 추가 학습 MP4의 byte-range 응답, replay JSON 응답 확인.
- loopback/Tailscale 인터페이스에서 HTTP 200, SSE 이벤트 수신, 수집 health 확인.
- 수집기·웹 서비스 재시작 전후 학습 지표 5,231행 유지: 중복 생성 없음.
- 브라우저에서 직접 클릭·레이아웃을 검수하는 테스트는 이번 검증에 포함하지 않았다.

```bash
.monitor-venv/bin/python -m unittest monitor.test_monitor -v
```

원본은 조회만 하며 `artifacts/`와 `result/`를 자동 삭제하지 않는다. DB 색인은 다시 만들 수 있지만 모니터링 시계열은 재구축되지 않는다. `.monitor/`, `.monitor-venv/`, `web/node_modules/`, `web/dist/`는 Git에서 제외한다. 서비스 로그는 user journal에 기록한다.

구현 참고: [Starlette 파일 응답·Range](https://starlette.dev/responses/), [Vite 환경 요구](https://vite.dev/guide/), [psycopg 트랜잭션](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).

## 갱신 동작 보완

실시간 데이터가 들어와도 그래프 인스턴스를 유지하고 series만 갱신해 확대·축소 및 범례 선택을 초기화하지 않도록 수정했다. 비교 화면의 평가 연결은 실행 이름 규칙 대신 checkpoint의 실제 출처 경로를 사용한다. 과거 수동 이름으로 실행한 평가도 표시하며 반복 평가는 개별 행으로 유지한다.

## 공인 인터페이스 배포 — 연구실 포트 규정

사용자 요청에 따라 웹을 18710으로 이동하고 모든 IPv4 인터페이스에서 수신한다. 서버 내부에서 loopback·공인 IP·Tailscale IP 모두 health HTTP 200을 확인했다. 외부 기기에서의 접속은 별도 확인이 필요하다. UFW 서비스는 active, 설정은 ENABLED=yes이며 규칙 조회·18710 허용은 root 권한이 없어 실행하지 못했다. 외부 접속이 차단되면 운영자가 `sudo ufw allow 18710/tcp`를 실행한다. 방화벽 전체 비활성화나 기존 규칙 변경은 수행하지 않았다.

## Phase 태그와 동작 진단

Phase·실험 단계·과제·목적을 조합해 실행·영상·원본 파일을 필터링한다. [태그 계약](research-phases.md), [첫 진단 결과](hopping-diagnosis-results.md). 새 진단 영상에는 25Hz 접촉력·접촉 상태·행동과 수직 속도를 기록하며, 정량 진단은 별도 200Hz NPZ로 계산한다. 기존 영상의 없는 채널을 채워 넣지는 않는다.

## 첫 착지·안정화 분리 표시 (2026-09-12)

정밀 도약 평가의 원본 episode 기록에서 네 발 첫 접촉 반경 충족 수와 기존 안정화 달성 수를 각각 표시한다. 전체 과제 성공과 별도 지표이며, 과제별 성공 계약 차이를 안내한다. episode 표에도 첫 접촉 충족 여부를 추가했다. 과거에 필드가 없던 과제는 기록 없음으로 표시한다. 기존의 포괄적 완주율 표기는 과제 성공률로 명확히 했다.

향후 evaluate.py 출력에는 first_touch_precise_episodes/stabilized_episodes/success_contract 요약도 저장된다. 기존 artifact는 수정하지 않는다. 사용자 지정 연구실 서버18710의 기존 배포 흐름으로 적용했다. TypeScript/Vite build와페이지·기존정밀평가API HTTP200을확인했으며,별도브라우저QA는수행하지않았다.

수평 도약 평가는 `by_distance`가 있을 때 거리별 성공·출발 영역·순수 비행 이동·첫 접촉·안정화 표를 표시한다. 기존 구현 확인 평가API에서0/5/10/15cm 각16개 집계를 확인했고 TS/Vite build 및 기존18710서버HTTP200을확인했다. 별도브라우저QA는수행하지않았다.


## 대량 기록 조회 최적화 (2026-09-12)

`/api/runs`, `/api/videos`는 이제 배열 대신 `{items,total,limit,offset,has_more}`를 반환한다. 기본24개/최대100개, `q`, 반복 `tag`, run의 `kind`/`status`/`training_run`은 DB에서 필터링한 뒤 정렬·페이지 처리한다. 파일 탐색은 기본50개씩 응답한다. 기존 API 직접 소비자는 배열 대신 items를 읽어야 한다.

초기 현황은 집계와 최근8개 run만 조회한다. 다른 탭의 목록은 해당 탭에서만 요청한다. 기본 데이터 갱신은10초,태그목록60초,비활성브라우저탭은자동갱신중지다. 경로변경/해제된fetch는AbortController로취소하고검색은300ms지연한다. 비교지표는cursor이후증분을수집하며매갱신전체history재조회하지않는다. 로그는로그탭에서만조회한다.

영상목록의episode상세배열을제거했다. 카드이미지는`/api/thumbnail`에서480×270이하JPEG로생성,동시변환2개/파일변경기반디스크캐시/브라우저5분캐시를적용한다. 원본영상·이미지는그대로다운로드가능하다. `.monitor/thumbnails`는재생성가능한캐시다. 차트모듈은사용하는구성만번들에포함한다.

로컬단회측정:실행목록1,390,566→48,777bytes(1.58→.29초),영상목록27,696,606→53,651bytes(2.23→.26초). 작은영상목록응답은24개페이지이므로전체조회와작업량이다르다. 초기JS raw1.39MB→.81MB. 썸네일샘플23,556bytes. 부하시험의p95나외부기기속도보장은아니다.

검증:격리PostgreSQL통합테스트9개통과,TS/Vite build통과,실제Chromium에서초기요청에videos없음/recentruns8개,목록24개/다음페이지/전체기록검색/영상재생화면/파일50개/비교화면검증,JS page error0. `artifacts/monitor-pagination-validation/`에기록. 기존user service18710배포반영.
