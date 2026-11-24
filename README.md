# 서울 분리배출 RAG

서대문구와 송파구 주민이 품목과 배출 상황을 질문하면 공식 문서의 근거와 출처를 안내하는 Knowledge Agent를 만든다. 필요한 조건은 되묻고, 자료에 답이 없으면 정보 부족을 알린다.

팀의 최종 목표는 Streamlit 화면, A/B/C 검색, 동 이름 인식, 질문 다듬기와 getSpot 장소 지도다. 화면과 평가 실행기가 같은 Python RAG 함수를 호출하도록 연결한다.

**2026-11-24 현재 실제 전처리 자료를 형식별로 색인하고 질문의 근거를 조회할 수 있다.** 제공된 XML은 HTML로 변환하고 전처리 JSON과 같은 원문 ID/버전으로 연결했다. `text-embedding-3-small`의 실제 색인을 만들었으며, 답변 생성과 팀 A/B/C 검색, Streamlit 연결은 남아 있다.

| 구분 | 현재 상태 |
| --- | --- |
| 문서 처리 | PR 8 전처리 묶음 검증, XML→HTML/JSON 문서 쌍, 조문/표 행 청킹과 형식별 실제 임베딩 색인 구현 |
| 공통 실행 | 팀 함수 연결, 지역별 근거 선택, 인용 검사, 실행 JSON 기록과 평가 실행기 구현 |
| 직접 실행 | 실제 색인의 근거 조회 CLI와 API 키 없는 합성 응답 데모 실행 가능 |
| 팀 기능 | 수집/전처리는 PR 8 결과 사용. A/B/C 검색, 지역/동 해석, 질문 변환 모델, 답변 LLM, 장소/지도, 품질 지표는 연결 전 |

파일별 구현 범위와 검증 결과의 기준 문서는 [공통 기반 최소 인계본](docs/seokho-handoff.md)이다. 검색/생성 연결 함수가 준비돼 있다는 사실과 실제 서비스가 동작한다는 사실을 구분한다.

## 개발 환경

이 README와 `scripts/chat.py`가 포함된 체크아웃 또는 인계 ZIP의 루트에서 실행한다. Python `3.13.14`, uv `0.13.9` 이상과 `uv.lock`을 사용한다. 로컬 변경의 완료와 원격 브랜치 반영은 별개다.

```sh
uv sync --locked
uv run --locked python --version
uv run --locked python -m pytest --version
```

로컬 uv가 요구 버전보다 낮으면 전역 설치를 바꾸지 않고 `uv tool run --from uv==0.13.9 uv sync --locked`로 같은 환경을 준비할 수 있다. 첫 설치는 Python 배포 서버와 PyPI 연결이 필요하다. 이 방식으로 설치했다면 실행도 `uv tool run --from uv==0.13.9 uv run --locked python --version`처럼 같은 uv 버전을 사용한다. 기존 Python 3.15 가상환경도 동기화하면 `.python-version`에 맞는 3.13.14 환경으로 다시 생성한다.

현재 의존성 파일은 루트의 공용 Python 환경을 관리한다. Streamlit, Selenium과 Langfuse 등 구현에 필요한 패키지는 해당 기능을 처음 연결하는 PR에서 의존성과 잠금 파일을 함께 갱신한다. 기존 FastAPI 의존성이 남아 있어도 별도 HTTP 서버 구현을 요구하지 않는다. 현재 `app.py`는 문서 문자열만 있는 뼈대이며 앱 실행 명령은 실제 화면 구현과 함께 추가한다.

## 실제 자료 준비와 근거 조회

수집과 HWP 전처리는 [PR 8](https://github.com/kssk3/best-driver-rag-project/pull/8)의 결과를 사용한다. v2 인계 ZIP을 따로 준비한 뒤 저장소 루트에서 실행한다. 아래 입력 경로는 보관 위치에 맞게 바꾸고 출력에는 아직 없는 폴더를 지정한다.

```sh
uv run --locked python -m scripts.prepare_data --bundle "C:/자료/p04_data_review_2026-11-24_v2.zip" --version v1 --output-dir data/processed/p04-v2-prepared
```

이 명령은 외부 호출 없이 공용 문서와 HTML/JSON 청크를 만든다. 실제 색인까지 만들려면 `OPENAI_API_KEY` 환경변수를 준비하고 `--openai-model text-embedding-3-small`을 추가한다. 기존 키 파일은 `--api-key-file`로 명시할 수도 있으며 `.env`는 자동 로드하지 않는다. 자료, 생성물과 키 파일은 Git에 넣지 않는다.

현재 로컬에서 검증한 실제 색인으로 반복 질문하려면 다음과 같이 실행한다. 새 체크아웃에서는 같은 출력 위치로 색인을 먼저 준비해야 한다.

```sh
uv run --locked python -m scripts.search_index --index data/processed/p04-v2-openai-small/index-html.json --index data/processed/p04-v2-openai-small/index-json.json --district 송파구
```

`--question "질문"`을 지정하면 한 번 조회하고, 생략하면 질문을 반복 입력한다. `/종료`로 끝낸다. 이 명령은 지역을 제한한 코사인 유사도 근거 조회이며 답변 LLM이나 팀 A/B/C 검색이 아니다. 실제 질문에서 관련 별표가 상위 결과에 빠진 사례가 있어 검색 품질은 개선이 필요하다. 결과와 한계, ID 유지 및 재실행 방법은 [실제 전처리 자료 연결](docs/seokho-handoff.md#실제-전처리-자료-연결)에 정리했다.

## 합성 자료로 응답 흐름 확인

```sh
uv run --locked python -m scripts.chat --demo
```

처음 구를 선택하고 아래 예시를 입력한다. 이 CLI는 대화 기록을 다음 질문에 전달하지 않으며, 문장에서 지역을 추론하지 않는다.

| 구/입력 | 확인할 동작 |
| --- | --- |
| 서대문구 선택 후 `품목알파` | 합성 조건엑스 안내와 출처 |
| `/구 송파구` 입력 후 `품목알파` | 합성 조건와이 안내와 출처 |
| `없는품목오메가` | 근거 부족 응답 |
| `공통시험품목` | 공통 합성 문서 안내 |
| `/구` 입력 후 구를 빈칸으로 두고 `품목알파` | 지역 확인 질문 |
| `/종료` | 실행 종료 |

`scripts.chat --demo`는 합성 자료 전용이다. 실제 자료의 근거 조회는 위 `scripts.search_index`를 사용한다. 합성 응답 실행 기록은 `results/local/chat-demo-<실행 식별자>/runs/`에 저장한다.

## 자동 데모와 검증

```sh
uv run --locked python -m scripts.demo
```

API 키 없이 합성 문서 3개로 색인부터 답변, 지역 재질문, 근거 부족과 실행 기록 저장까지 확인한다. 실행할 때마다 `results/local/handoff-demo-<실행 식별자>/`에 색인과 결과 JSON을 만든다. 해시 임베딩과 본문 인용을 사용하는 연결 검사이며 실제 분리배출 안내나 검색 품질 평가 결과가 아니다.

테스트 실행과 CI 설정은 [검사와 의존성 관리](docs/CI-AND-DEPENDENCIES.md), 실제로 확인한 결과는 [인계본 검증 기록](docs/seokho-handoff.md#구현-경계와-검증)에 있다. 단위/CLI 검증은 최종 20문항의 실제 품질 평가를 대신하지 않는다.

입력 자료 규격, 색인/평가 명령과 팀 함수 연결 예시는 [인계 문서](docs/seokho-handoff.md)에 있다. `sources.json`은 문서 목록과 첨부 관계를 읽는 별도 입력이며 전처리 묶음 대신 넣지 않는다. OpenAI 임베딩 환경변수는 [.env.example](.env.example)을 참고한다.

## 작업 위치

| 경로 | 용도 |
| --- | --- |
| `src/` | 공통 실행 기반과 담당별 Python 모듈 |
| `configs/`, `prompts/`, `.streamlit/` | 공통 설정, 프롬프트와 화면 설정 |
| `scripts/` | 수집, 색인과 평가 실행 진입점 |
| `data/` | 수집 원문, 정제 자료와 색인 |
| `eval/` | 개발 10문항과 최종 20문항, 정답 및 허용 근거 |
| `results/` | 실행 원본, 평가와 비교 결과 |
| `tests/` | 단위 검사, 연동 검사와 작은 검증 자료 |

상세 파일 목록, 담당 경로와 연결 원칙은 [구조와 책임](docs/architecture.md)에 있다. 파일별 구현 항목과 플로우 차트는 [Notion 구조 문서](https://app.notion.com/p/422dc8b0e1638150b62acfe703074f30?pvs=204)에서 확인한다. 폴더의 `.gitkeep`은 빈 작업 위치를 Git에 보존하기 위한 파일이다.

## 팀 공통 문서

- [문제와 평가 기준](docs/problem.md): 지원 범위, 평가 분리와 완료 기준
- [공동 진행 단계](ROADMAP.md): 7단계와 병렬 작업 흐름
- [개발 환경과 연결 기준](docs/TEAM-SETUP.md): 공용 규격과 인계 방식
- [검사와 의존성 관리](docs/CI-AND-DEPENDENCIES.md): pytest, Codecov, Dependabot과 Gitleaks
- [출처 목록 로더](docs/source-manifest-loader.md): `sources.json` 필드와 첨부 관계 읽기
- [공통 기반 최소 인계본](docs/seokho-handoff.md): 입력 규격, API, 실행 명령, 현재 한계와 검증 결과

통합 기준 브랜치는 `dev`다. 작업 브랜치는 `feature/<작성자>/<작업명>`으로 만들고, 검증 후 `dev`를 대상으로 PR을 연다. 합성 검증 자료는 `tests/fixtures/`에 있으며 실제 최종 평가셋과 품질 평가 결과는 포함되어 있지 않다.
