# 팀 개발 환경과 API 계약

[4일 로드맵](../ROADMAP.md)과 [커버리지·의존성 관리 안내](CI-AND-DEPENDENCIES.md)를 함께 사용합니다. 아래 경로는 구현 때 만들 파일의 위치입니다. 첫 통합 목표는 DB나 모델 인증 정보 없이 브라우저의 요청이 Python API까지 도달해 JSON 응답을 받는 것입니다.

## 담당자별 첫 작업

| 담당자 | 담당 경로 | 바로 시작할 일과 인계 결과 |
| --- | --- | --- |
| 양석호 · 통합 | `backend/api/`, `backend/chat/`, `backend/domain/`, `backend/main.py`, `contracts/`, Compose, CI | 아래 응답 예시 4개를 배포합니다. 고정된 값을 돌려주는 검색기와 생성기를 연결하고, 통합 때 실제 구현으로 교체합니다. |
| 이정은 · 수집 | `backend/ingestion/` | 구청 원문 1건과 공통 품목 1건부터 시작합니다. 규칙당 한 줄의 JSONL과 자치구별 수집 상태표를 넘깁니다. |
| 이명지 · DB·검색 | `backend/retrieval/`, `supabase/migrations/` | 샘플을 적재하고 조건에 맞는 청크를 최대 3개 반환합니다. 같은 자료를 두 번 적재해도 ID와 건수가 유지되어야 합니다. |
| 강성수 · 답변·평가 | `backend/answers/`, `evaluation/` | 아래 응답 예시의 검색 후보로 시작합니다. 인용 근거를 추적할 수 있는 응답과 로드맵의 평가 사례를 넘깁니다. |
| 이승주 · UI | `frontend/` | 네 가지 응답을 화면으로 구현한 뒤 `POST /api/chat`에 연결합니다. 추가 질문 시 최초 질문과 자치구를 보존합니다. |

## 폴더와 4계층 경계

평가 담당자는 `evaluation/`에 평가 실행 코드를 두고, 수업 제출 형식인 `eval/dev.json`과 `eval/test.json`에는 고정 문항만 둡니다. 검색 담당자는 구성별 상위 5개의 청크 ID와 원문 위치를 `results/`에 기록하고 화면과 생성 모듈에는 최대 3개를 넘깁니다. API의 합성 예시는 형식 확인용입니다. 실제 수집·인용은 문서 ID, 청크 ID, 절·행 또는 발췌까지 추적할 수 있어야 합니다. [문제와 평가 계약](problem.md)

~~~text
contracts/chat/                  요청·응답 JSON 예시
backend/
  main.py                        어댑터 조립과 ASGI 진입점
  api/chat.py                    표현 · HTTP 검증과 응답 변환
  chat/ask.py                    응용 · 검색과 답변 흐름
  domain/models.py               도메인 · 질문, 검색 후보, 답변 결과
  domain/ports.py                도메인 · 검색·생성 인터페이스
  ingestion/collect.py           응용 · 일괄 수집과 규칙 정제
  ingestion/adapters/            인프라 · 구청 원문과 품목 API
  retrieval/                     인프라 · SQL, 임베딩, 재정렬
  answers/                       인프라 · GPT와 근거 연결
  tests/                         도메인·유스케이스·HTTP·어댑터 테스트
  Dockerfile
frontend/
  src/app/page.tsx                자치구 선택·FAQ·결과 화면
  src/components/                 추가 질문 입력·개발자 패널
  src/lib/chat.ts                 타입을 정의한 HTTP 클라이언트
  next.config.ts
  package.json
  package-lock.json
  Dockerfile
supabase/migrations/              DB·검색 담당자의 스키마 변경 이력
evaluation/                      구별 기본 동작과 품질 평가
compose.yaml
pyproject.toml                     백엔드 실행·개발 의존성
.python-version                    Python 인터프리터 버전
uv.lock                            전이 의존성까지 포함한 잠금 파일
.env.example
~~~

Python 패키지 디렉터리에는 `__init__.py`를 둡니다. 저장소 루트에서 실행하고 `from backend.domain.models import Question`처럼 패키지 경로로 가져옵니다. 백엔드는 루트의 uv 설정을 읽기 위해 저장소 루트를 빌드 컨텍스트로 사용하고, 프론트엔드는 자체 폴더를 사용합니다.

| 백엔드 계층 | 참조할 수 있는 대상 | 첫 구현과 책임 |
| --- | --- | --- |
| 표현 | 응용·도메인 | `api/chat.py`가 공백 질문을 거르고 서울 자치구명을 검증합니다. HTTP 요청을 도메인 객체로, 처리 결과를 JSON으로 변환합니다. |
| 응용 | 도메인 타입·인터페이스 | `chat/ask.py`가 검색기와 생성기를 인자로 받습니다. 후보가 없으면 근거 부족을 반환합니다. 후보가 있으면 생성을 호출하고, 인용 ID가 실제 후보에 포함됐는지 확인합니다. |
| 도메인 | Python 표준 라이브러리 | 질문, 적용 조건, 후보, 응답 상태, 인터페이스를 정의합니다. 지역 규칙은 사용자가 선택한 구의 근거가 필요합니다. 공통 품목 자료로 구별 배출 일정을 확정할 수 없습니다. |
| 인프라 | 도메인 계약·외부 라이브러리 | SQL·임베딩·크롤러·GPT 어댑터를 구현합니다. `main.py`에서 실제 어댑터를 선택해 응용 계층에 전달합니다. |

`backend/domain/ports.py`의 시작점은 아래 두 인터페이스입니다. `domain/models.py`의 세 데이터 타입은 아래 JSON의 필드를 기준으로 정의합니다. 공통 인터페이스 변경은 통합 담당자가 관리합니다.

~~~python
from typing import Protocol

from backend.domain.models import Candidate, ChatResult, Question


class Retriever(Protocol):
    def search(self, question: Question) -> list[Candidate]: ...


class AnswerGenerator(Protocol):
    def answer(self, question: Question, candidates: list[Candidate]) -> ChatResult: ...
~~~

## 버전 기준과 초기 환경 준비

2026년 11월 23일 공식 배포 기준은 **Python 3.15.2**, **Next.js 16.4.6**, **Node.js 26.13.1 LTS**입니다. 로컬·컨테이너·CI에 같은 버전을 쓰고, npm 잠금 파일과 Python의 uv 잠금 파일을 버전 관리합니다. [Python 공식 릴리스](https://www.python.org/downloads/source/) · [Next.js npm 배포 정보](https://registry.npmjs.org/next/latest) · [Node.js 공식 다운로드](https://nodejs.org/en/download)

저장소 루트에서 아래 명령으로 UI를 생성합니다. `frontend/`에 팀의 Vitest 설정이 이미 있으므로, 빈 임시 폴더에서 Next.js 기본 파일을 생성한 뒤 기존 파일을 보존하며 복사합니다. 생성된 `src/app/`의 루트 레이아웃을 사용하고 설치 결과와 잠금 파일을 확인합니다.

~~~sh
scaffold_dir=$(mktemp -d)
npx --yes create-next-app@16.4.6 "$scaffold_dir/frontend" --ts --app --src-dir --use-npm --eslint --skip-install --disable-git --yes
cp -Rn "$scaffold_dir/frontend/." frontend/
cd frontend
npm install --save-exact next@16.4.6
npm ls next react react-dom
~~~

백엔드 환경은 저장소 루트에서 `uv sync`로 준비합니다. 인터프리터·의존성 파일의 역할, uv 설치 조건과 실행 확인 명령은 [README의 Python 시작 절차](../README.md#python-개발-환경)에 있습니다. 팀원이 패키지를 추가할 때는 `uv add 패키지명`을, 테스트 도구에는 `uv add --dev 패키지명`을 사용하고 `pyproject.toml`과 `uv.lock`을 함께 커밋합니다.

`backend/main.py`에 FastAPI의 `app`을 만들고 `POST /chat`을 노출합니다. 처음에는 빈 목록을 반환하는 검색기를 주입합니다. 그러면 외부 인증 없이 유효한 요청이 전체 HTTP 경로를 거쳐 `insufficient_evidence`로 끝나는지 확인할 수 있습니다. UI는 그 전부터 아래 고정 응답으로 개발할 수 있습니다.

## 수집 데이터와 POST /chat 계약

아래 데이터는 팀 개발용 가상 규칙입니다. 실제 적재 시에는 확인한 공식 URL, 원문 구절, 자치구, 적용 조건, 확인일을 보존합니다. 공통 품목의 `district`는 JSON `null`입니다. 수집 담당자가 넘길 레코드 한 줄의 예입니다.

~~~json
{"document_id":"fixture-sdm-01","source_url":"https://example.org/fixture/sdm","checked_at":"2026-11-23","district":"서대문구","item":"생활쓰레기","conditions":{"dong":"연희동"},"text":"예시 규칙 A는 이 동에 적용됩니다."}
~~~

브라우저는 Next.js와 같은 주소의 `/api/chat`으로 JSON을 보냅니다. Python이 받는 경로는 `POST /chat`입니다. 필수 필드는 `question`과 `district`, 선택 필드는 `dong`과 `housing_type`입니다. 아래 두 예시는 최초 질문과 추가 정보 입력 후의 재요청입니다.

~~~json
{"question":"생활쓰레기 배출 기준을 알려줘","district":"서대문구"}
~~~

~~~json
{"question":"생활쓰레기 배출 기준을 알려줘","district":"서대문구","dong":"연희동"}
~~~

**조건 확인 · HTTP 200.** `required_fields`에 해당하는 입력란을 표시하고 원래 요청에 값을 더해 다시 전송합니다.

~~~json
{"status":"needs_clarification","answer":"어느 동의 배출 기준을 확인할까요?","required_fields":["dong"],"sources":[],"candidates":[]}
~~~

**답변 완료 · HTTP 200.** `sources`에 있는 ID와 일치하는 후보를 화면에 ‘인용됨’으로 표시합니다. 검색 점수·순위와 답변에서 실제로 사용한 근거를 구별할 수 있습니다.

~~~json
{
  "status": "answered",
  "answer": "예시 자료에서 연희동에 적용되는 항목은 규칙 A입니다.",
  "required_fields": [],
  "sources": [{"chunk_id":"fixture-sdm-01-1","source_url":"https://example.org/fixture/sdm"}],
  "candidates": [{
    "chunk_id":"fixture-sdm-01-1","text":"예시 규칙 A는 이 동에 적용됩니다.",
    "district":"서대문구","conditions":{"dong":"연희동"},
    "source_url":"https://example.org/fixture/sdm","retrieval_score":0.89,"rerank_rank":1
  }]
}
~~~

**근거 부족 · HTTP 200.** 자치구 규칙이 미확인이거나 자료의 기간 충돌을 사용자의 추가 정보로 해소할 수 없을 때 반환합니다.

~~~json
{"status":"insufficient_evidence","answer":"확인된 공식 자료만으로는 배출 기준을 확정할 수 없습니다.","required_fields":[],"sources":[],"candidates":[]}
~~~

**외부 서비스 오류 · HTTP 503.** UI는 HTTP 실패 응답에서도 JSON을 읽어 안내를 표시합니다. 필수 필드 누락 등 요청 검증 실패는 HTTP 422로 따로 처리합니다.

~~~json
{"status":"error","answer":"검색 서비스에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.","required_fields":[],"sources":[],"candidates":[]}
~~~

## 컨테이너와 공유 Supabase

**`backend/Dockerfile`**은 `/srv/backend`에 Python 패키지를 배치합니다. 의존성을 먼저 설치하면 라우트 파일만 수정할 때 설치 레이어를 재사용할 수 있습니다.

~~~dockerfile
FROM python:3.15.2-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv
WORKDIR /srv
COPY .python-version pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
ENV PATH="/srv/.venv/bin:$PATH"
COPY backend/ /srv/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
~~~

**`frontend/Dockerfile`**은 Next.js 개발 서버를 실행합니다. `frontend/.dockerignore`에 `node_modules`, `.next`, `.env*`, `coverage`를 넣습니다. 백엔드용 루트 `.dockerignore`에서도 `.venv`, `__pycache__`, `.env*`와 커버리지 결과물을 빌드 컨텍스트에서 제외합니다.

~~~dockerfile
FROM node:26.13.1-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
~~~

**`frontend/next.config.ts`**는 브라우저 요청을 Python으로 전달합니다. Compose 안에서는 서비스 이름을, 프론트만 호스트에서 띄울 때는 로컬 주소를 사용합니다.

~~~typescript
import type { NextConfig } from "next";

const config: NextConfig = {
  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";
    return [{ source: "/api/chat", destination: `${origin}/chat` }];
  },
};

export default config;
~~~

**`compose.yaml`**은 두 개발 서버를 띄웁니다. 소스 디렉터리를 마운트해 수정 사항을 반영하고, npm 의존성은 이미지에 보관합니다. 의존성이나 Next.js 설정을 바꾸면 이미지를 다시 빌드합니다.

~~~yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    env_file: ./.env
    ports: ["127.0.0.1:8000:8000"]
    volumes: ["./backend:/srv/backend"]
    command: ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/srv/backend"]
  frontend:
    build: ./frontend
    environment:
      BACKEND_ORIGIN: http://backend:8000
    ports: ["127.0.0.1:3000:3000"]
    volumes: ["./frontend/src:/app/src"]
~~~

**루트 `.env.example`**은 팀에서 사용할 백엔드 연결 형식입니다. Supabase 대시보드의 연결 메뉴(Connect)에서 해당 프로젝트의 세션 풀러(Session pooler) 연결 주소를 복사해 실제 호스트와 포트를 사용합니다. SQL 어댑터는 `DATABASE_URL`을 직접 읽습니다. 실행용 역할에는 담당 작업에 필요한 권한을 부여하고 스키마 변경은 DB 담당자의 마이그레이션 연결로 수행합니다. [Supabase 연결 가이드](https://supabase.com/docs/guides/database/connecting-to-postgres)

~~~dotenv
# 예시 데이터 모드는 외부 인증 없이 시작합니다.
RAG_MODE=fixture
# 실제 데이터 모드는 세션 풀러 연결 주소를 사용하고 비밀번호는 URL 인코딩합니다.
DATABASE_URL=postgresql://ROLE.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres?sslmode=require
OPENAI_API_KEY=
CHAT_MODEL=
EMBEDDING_MODEL=
~~~

`main.py`는 `RAG_MODE`에 따라 어댑터를 선택하고 `live` 모드에서 연결값을 검증합니다. DB 벡터 열의 차원은 선택한 임베딩 모델 출력과 일치시킵니다. 루트 `.env`는 백엔드에서만 읽습니다. Git에는 `.env`와 `.venv/`를 제외하고 예시 파일만 포함합니다.

**첫 통합 확인.** 진입점·UI·의존성 파일을 만든 뒤 저장소 루트에서 실행합니다. 빈 검색기를 쓰면 두 포트 모두 HTTP 200과 `insufficient_evidence`를 반환해야 합니다. 실제 어댑터로 전환한 뒤에는 구 규칙 1건과 공통 품목 1건으로 반복하고 인용된 원문을 엽니다.

~~~sh
if [ ! -e .env ]; then
  cp .env.example .env
fi
docker compose config --quiet
docker compose up --build -d
curl -sS http://localhost:8000/chat -H 'Content-Type: application/json' \
  -d '{"question":"생활쓰레기 배출 기준을 알려줘","district":"서대문구"}'
curl -sS http://localhost:3000/api/chat -H 'Content-Type: application/json' \
  -d '{"question":"생활쓰레기 배출 기준을 알려줘","district":"서대문구"}'
~~~
