# 공통 기반 최소 인계본

이 문서는 양석호 담당 공통 기반을 팀 코드에 연결하는 방법과 현재 구현 범위를 설명한다. 로컬 파일과 합성 자료로 호출 흐름을 확인하는 인계본이며, 실제 분리배출 서비스의 검색 품질이나 운영 준비를 입증하는 결과는 아니다. 담당 구분의 기준은 [구조와 책임](architecture.md), 팀 연결 규칙은 [공동 입출력](TEAM-SETUP.md)에 둔다.

## 처음 실행하기

저장소 루트에서 실행한다. 프로젝트 환경은 Python 3.13.14이며 `uv` 0.13.9 이상을 사용한다. 다음 명령의 `uv run`은 프로젝트 가상환경을 사용한다.

```powershell
uv sync --frozen
uv run python -m scripts.demo --output-dir results/local/handoff-demo
```

데모는 합성 문서, 외부 API를 호출하지 않는 해시 임베딩과 원문 인용 생성기를 사용한다. API 키가 필요하지 않다. 데모 성공은 파일 읽기, 색인, 공통 호출과 기록 연결을 확인하는 것이며, 의미 검색이나 실제 LLM 답변 성능의 증거가 아니다.

출력 폴더에는 `index.json`, `summary.json`, `runs/<run_id>.json`이 생성된다. `--output-dir`에는 아직 없는 폴더를 지정한다. 반복 실행에서 기존 결과를 지우지 않으려면 다른 폴더를 지정하거나 옵션을 생략해 자동 생성되는 실행별 폴더를 사용한다.

색인과 평가를 따로 실행할 때는 다음 진입점을 사용한다.

```powershell
uv run python -m scripts.index --documents tests/fixtures/handoff_documents.json --output data/indexes/demo.json --demo --dimensions 128
uv run python -m scripts.evaluate --cases tests/fixtures/handoff_eval.json --output-dir results/local/handoff-eval --demo --settings configs/demo.json
```

`--documents`에는 공용 `SourceDocument` 목록을 지정한다. 출처 목록인 `sources.json`, 검수 ZIP 전체와 평가 정답표는 이 입력에 넣지 않는다. 색인은 명시한 출력 파일을 교체하며, 입력 문서와 출력 색인 경로는 달라야 한다. `data/indexes/`와 `results/local/`의 생성물은 Git 추적 대상에서 제외된다.

평가 명령은 앞서 만든 색인을 읽으며 자동으로 다시 만들지 않는다. 평가 출력 폴더도 아직 없어야 하고, `evaluation.json`과 `runs/<run_id>.json`이 생성된다. 위 색인 명령은 128차원을 명시했으며, 데모 질의 임베더는 설정값 대신 실제 색인 메타데이터의 차원으로 생성하고 provider identity를 확인한다.

HTML/JSON 비교용 입력은 `scripts.index --content-format html` 또는 `--content-format json`으로 서로 다른 색인 파일에 저장할 수 있다. 형식별 분리만으로 동등한 내용이나 성능 비교가 검증되는 것은 아니다.

## 직접 질문 입력

```powershell
uv run --locked python -m scripts.chat --demo
```

구를 입력한 뒤 질문을 계속 입력한다. `품목알파`는 구별 합성 안내를 반환하고, `공통시험품목`은 공통 합성 문서를 사용한다. `없는품목오메가`는 근거 부족을 확인하는 예시다. `/구 송파구` 또는 `/구`로 지역을 변경하고 `/종료`로 종료한다. 빈 질문은 건너뛰며 Ctrl+C와 입력 종료도 지원한다.

각 질문은 독립 처리하므로 이전 질문이나 추가 확인 답변을 이어서 해석하지 않는다. 실제 분리배출 규칙과 LLM은 연결되어 있지 않다. 색인은 합성 문서로 자동 준비하며 원본 기록은 실행마다 새로운 `results/local/chat-demo-<실행 식별자>/runs/`에 남긴다. 터미널에서는 HTML 태그를 읽기 쉬운 문자열로 표시하고 기록에는 원본 응답을 보존한다. `--output-dir`를 직접 지정하면 아직 존재하지 않는 폴더여야 한다.

## 자료를 교체하는 방법

입력은 역할에 따라 세 가지로 구분한다.

| 입력 | 함수 | 반환과 범위 |
| --- | --- | --- |
| `sources.json` 형식의 문서 목록 | `load_source_manifest(path)` | `list[SourceManifestEntry]`. 조례/시행규칙과 첨부 링크의 포함 관계를 보존한다. 본문을 다운로드하거나 생성하지 않는다. |
| 메타데이터와 본문을 갖춘 공용 문서 JSON | `load_source_documents(path)` | `list[SourceDocument]`. JSON 배열 또는 `documents` 목록 포장을 읽는다. |
| 전처리된 HTML/JSON 본문 파일 한 개 | `load_preprocessed_content(path, metadata=...)` | `SourceDocument`. 파일 본문과 호출자가 제공한 출처 정보를 연결한다. |

세 함수는 `src/ingestion/loaders.py`에 있다. 폴더를 자동 탐색하지 않으며, 지정한 파일만 읽는다. UTF-8과 UTF-8 BOM을 지원한다. 목록의 `본문_파일`은 기재된 경로이며 파일 보관 완료를 뜻하지 않는다.

단일 전처리 파일을 연결하는 예시는 다음과 같다. 아래 ID와 버전, URL은 합성 예시다. 실제 자료의 ID 발급과 개정 이력 관리는 로더가 수행하지 않는다.

```python
from src.ingestion.loaders import load_preprocessed_content

document = load_preprocessed_content(
    "data/processed/example-annex.html",
    metadata={
        "document_id": "synthetic-annex-2",
        "version": "synthetic-revision-1",
        "title": "합성 별표 안내",
        "source_url": "https://example.org/annex-2.hwp",
        "scope_type": "district",
        "districts": ["서대문구"],
        "parent_document_id": "synthetic-ordinance",
        "parent_document_version": "synthetic-parent-revision-1",
    },
)
```

`content_format`은 `.html`/`.json` 확장자에서 정하고, `content`는 파일 문자열을 보존한다. 두 필드는 `metadata`로 덮어쓸 수 없다. `raw_path`를 생략하면 기존 모델의 기본값 `None`을 유지한다. 이 경로는 전처리 파일 경로가 아니라 실제 보관한 원본의 프로젝트 상대 경로이며, 로더가 임의로 채우지 않는다.

공용 문서 목록은 `SourceDocument` 필드의 JSON 객체들을 배열에 넣는다. 합성 fixture처럼 `{"documents": [...], "is_synthetic": true, "description": "..."}` 형태도 지원한다. 문서 ID, 버전, 표현 형식이 모두 같은 항목은 중복으로 거부한다. 같은 원문의 HTML/JSON 표현은 원문 ID/버전을 공유하고 형식으로 구분할 수 있다.

기존 `SourceDocument` 클래스와 의미는 유지했다. 부모 ID와 버전의 참조 형태를 검사하지만, 부모가 별도 파일에 있을 수 있어 이 로더에서 부모 존재를 강제하지 않는다. HTML은 요소 존재와 명백한 잘림을 검사하는 수준이다. JSON 파싱과 문자열 보존이 원문 의미나 표/각주의 완전한 검수를 대신하지는 않는다. HWP/PDF 추출과 검수 ZIP의 초안 JSON을 공용 문서로 변환하는 전용 어댑터는 포함하지 않는다.

## 청킹과 색인

```python
from src.ingestion.chunking import chunk_documents
from src.ingestion.indexing import MemoryEmbeddingCache, build_index
from src.infrastructure.embeddings import DemoHashEmbeddings
from src.infrastructure.stores import save_index

chunks = chunk_documents([document], max_characters=20_000)
cache = MemoryEmbeddingCache()
index = build_index(chunks, DemoHashEmbeddings(dimensions=64), cache=cache)
save_index(index, "data/indexes/example.json")
```

현재 `chunk_documents`는 문서 전체를 하나의 청크로 만든다. 임의의 문자 분할로 표의 공통 비고와 예외 조건이 떨어지는 것을 피하기 위한 최소 구현이다. 기본 한도 20,000자는 Python 문자열의 문자 수이며 모델 토큰 한도가 아니다. 초과하면 문서 ID를 포함한 오류를 내고 자동 분할하거나 일부를 버리지 않는다. 큰 자료에는 표/별표 등 논리 단위 분할을 별도로 구현해야 한다.

청크는 원문 ID/버전, 표현 형식, 제목, 본문, URL과 적용 지역을 보존하며 `source_location`은 현재 `"문서 전체"`다. `conditions=[]`는 별도 조건 추출을 하지 않았다는 뜻이다. 본문에 있는 조건과 예외는 삭제하지 않는다. 청크 ID는 원문 ID/버전, 표현 형식, 본문, 출처 URL과 청킹 버전으로 결정하므로 동일 입력과 규칙에서는 재실행해도 유지된다.

`EmbeddingProvider`는 `identity`, `embed_documents(texts)`, `embed_query(text)` 경계다. 기존 LangChain 임베더는 `LangChainEmbeddingsAdapter`로 연결할 수 있다. 모델, 차원과 벡터에 영향을 주는 설정이 바뀌면 `identity`도 바꿔야 한다. 실제 OpenAI 연결을 선택할 때는 `create_openai_embeddings(model, dimensions=...)` 또는 색인 CLI의 `--openai-model`을 사용한다. 인계 데모에서는 이 경로를 사용하지 않는다.

임베딩 캐시는 같은 provider identity와 정확히 같은 본문의 벡터를 재사용한다. 본문이 같아도 출처별 청크는 합치지 않는다. `MemoryEmbeddingCache`는 같은 객체를 넘긴 동안만 유지되며, 프로세스 간 영구 캐시가 아니다.

`build_index`는 전달받은 전체 청크로 새 스냅샷을 만든다. 기존 색인과 자동 병합하거나 증분 삭제하지 않는다. 로컬 JSON에는 벡터, 청크, 임베딩 identity, 차원, 청킹 버전과 원문 버전 목록이 저장된다. `save_index`는 내용을 검증한 다음 임시 파일을 거쳐 지정 파일을 원자적으로 교체한다. 실제 DB와 벡터 저장소는 연결하지 않았다.

## 공용 규격과 팀 연결

공용 타입은 `src/contracts.py`에서 가져온다. 각 담당자가 동일한 구조를 별도 정의하지 않는다.

| 경계 | 공용 타입 |
| --- | --- |
| 문서와 검색 근거 | `SourceDocument`, `Chunk`, `SearchCandidate` |
| 사용자 요청과 해석된 검색 질의 | `PipelineRequest`, `ResolvedQuery`, `PipelineOptions` |
| 생성 결과와 최종 응답 | `GenerationResult`, `Citation`, `PipelineResponse` |
| 별도 장소 조회 | `PlaceResult`, `PlaceLookupResult` |
| 실행과 평가 입력 | `StageRecord`, `RunRecord`, `EvaluationCase` |

`PipelineOptions.variant`의 A/B/C는 연결할 검색 방식의 선택값이다. 공용 타입이 이 값을 받는다는 사실만으로 팀의 Vector, Hybrid, reranker가 구현된 것은 아니다. 응답 상태는 `answered`, `needs_clarification`, `insufficient_evidence`, `error`를 구분한다. 장소는 문서 청크와 별도 결과로 전달하며, 좌표나 수거 가능한 품목을 추정해서 채우지 않는다.

평가의 `reference_answer`와 `allowed_chunk_ids`는 사후 비교용이다. 검색/질문 변환/생성 입력에 넣지 않는다. 검색 후보, 실제 생성 입력 청크와 실제 인용 근거도 각각 구분해 기록한다.

`src/runtime.py`의 `create_runtime`에 각 담당자의 함수를 주입한다. 콜백 호출 규격은 다음과 같다.

| 인수 | 호출 규격 | 담당 연결 지점 |
| --- | --- | --- |
| `resolver` | `(PipelineRequest) -> ResolvedQuery` | 지역/동 해석과 추가 확인 필요 여부 |
| `rewriter` | `(ResolvedQuery) -> str` | 조건을 보존한 검색 질의 변환, 생략 가능 |
| `retriever` | `(ResolvedQuery, *, variant, top_k) -> list[SearchCandidate]` | A/B/C 검색 구현 |
| `generator` | `(PipelineRequest, list[Chunk]) -> GenerationResult` | 원질문과 실제 입력 근거를 사용한 답변/인용 ID |
| `place_lookup` | `(PipelineRequest, ResolvedQuery) -> PlaceLookupResult` | 장소 조회, 생략 가능 |

다음은 준비된 팀 함수를 받는 연결 함수 예시다. 실제 모델이나 DB는 콜백을 만드는 담당 코드에서 준비한다.

```python
from src.config import load_settings
from src.runtime import create_runtime

def connect_team_modules(*, resolver, retriever, generator,
                         rewriter=None, place_lookup=None):
    settings = load_settings()
    # 실제 실행에 사용한 데이터/색인/모델/프롬프트 버전은
    # settings.pipeline.versions에 넣는다. API 키는 넣지 않는다.
    return create_runtime(
        settings,
        resolver=resolver,
        retriever=retriever,
        generator=generator,
        rewriter=rewriter,
        place_lookup=place_lookup,
    )
```

연결된 `pipeline`은 UI와 평가에서 동일하게 사용한다. `run`의 반환값은 응답만이 아니라 `RunRecord`다.

```python
from src.contracts import PipelineRequest

record = pipeline.run(PipelineRequest(question="사용자 질문", district="서대문구"))
response = record.response
print(response.status, response.answer)
```

파이프라인은 지역 확인, 선택적 질의 변환, 검색, 생성 입력 선택, 생성과 인용 검사를 수행한다. 지역 확인이 필요하면 뒤 단계를 건너뛴다. 질의 변환이 실패하면 이전 검색 질의를 사용하고 경고를 남긴다. 생성 입력에서는 지역 미확인 청크와 다른 지역의 청크를 제외하며, 문맥 문자 수 한도를 넘으면 청크 전체를 제외한다. 이 한도는 `PipelineOptions.max_context_chars`이고 토큰 한도가 아니다.

`answered`에는 실제 생성 입력에 포함된 청크의 인용 ID가 필요하다. 검색 후보에만 있던 ID를 인용하면 `error`로 기록한다. 장소 조회 실패는 `response.places`의 상태로 별도 표시한다. 지역/품목 조건의 의미 판단과 근거 부족 응답 정책은 주입한 콜백의 책임도 포함하므로, 이 흐름만으로 답변 정확성을 보장하지 않는다.

## 설정, 실행 기록과 평가

`load_settings(path=None, project_root=None)`은 명시한 JSON 설정을 `RuntimeSettings`로 읽는다. 설정을 생략하면 모델 기본값을 사용한다. `index_path`와 `runs_path`의 상대 경로 기준은 `project_root` 또는 현재 작업 폴더다. API 키와 비밀값은 이 JSON이나 실행 기록에 넣지 않고 제공자 환경변수로 전달한다.

| 설정 | 의미 |
| --- | --- |
| `index_path` | 사용할 로컬 색인 파일 |
| `runs_path` | 실행 원본 JSON을 저장할 폴더 |
| `max_document_characters` | 문서 전체 청킹의 문자 수 한도 |
| `demo_dimensions` | `scripts.demo`에서 새 색인을 만들 때 사용할 데모 임베딩 차원 |
| `pipeline` | 검색 변형, 질의 변환 사용, top-k, 생성 입력 문자 한도와 실행 버전 |

`create_runtime`은 콜백과 기록기를 연결하며 자동으로 실제 DB나 모델을 생성하지 않는다. `RunRecorder`는 실행마다 `<run_id>.json`을 생성하고 같은 실행 ID 파일을 덮어쓰지 않는다. 기록에는 원질문, 해석된 지역과 질의(`resolved_query`), 실제 검색 질의, 후보, 생성 입력 ID, 답변/인용, 단계별 상태와 시간이 들어간다. `RunRecord.duration_ms`는 기록 파일 저장 전까지의 파이프라인 시간이다. 토큰 사용량, API 비용과 Langfuse trace는 현재 자동 수집하지 않는다.

`load_evaluation_cases(path)`는 평가 문항 배열 또는 `{"is_synthetic": true, "cases": [...]}` 포장을 읽는다. `evaluate_cases(cases, pipelines)`는 구성 이름을 키로 하는 파이프라인 딕셔너리를 받아 모든 문항/구성을 실행하고, `case_id`, 구성 이름, 실제 실행 ID, 응답과 원본 기록을 반환한다. 호출 실패도 `error` 결과로 남긴다. Ragas나 Hit@5를 계산하지 않으며, 반환된 실제 결과에 후속 평가를 붙이는 경계다.

실제 팀 함수를 평가 CLI에 연결할 때는 `--demo` 대신 `--factory 모듈명:함수명`을 지정한다. 이 함수는 `RuntimeSettings`를 인자로 받고 `RAGPipeline` 한 개 또는 구성 이름을 키로 하는 `dict[str, RAGPipeline]`을 반환해야 한다. 평가 파일에서 실행 코드를 읽지 않으며, 명령행에 명시한 연결 함수만 불러온다. 서로 다른 설정을 비교하려면 연결 함수가 각 설정의 파이프라인을 만들어 반환한다. 데모의 `--demo` 경로는 합성 구성 한 개를 실행한다.

`create_demo_pipeline(settings)`는 이미 저장된 데모 색인을 읽고, 해시 벡터와 간단한 단어 포함 조건으로 후보를 선택한다. A 호출 형태만 지원하며 실제 팀 A 검색 품질 구현은 아니다. 데모의 질의 변환은 공백 정리이고, 생성기는 첫 근거 본문을 표시한다. B/C 검색, 실제 질문 변환과 답변 모델의 성능을 대신하지 않는다.

## 파일별 인계 범위

| 파일 | 제공하는 역할 | 교체하거나 연결할 부분 |
| --- | --- | --- |
| `src/contracts.py` | 공용 문서/청크/요청/응답/기록 타입 | 팀 함수의 입출력에서 공통으로 사용 |
| `src/ingestion/loaders.py` | 출처 목록과 명시적인 공용 문서 파일 읽기 | 실제 전처리 결과에서 공용 규격으로의 변환 |
| `src/ingestion/chunking.py` | 문서 전체 청크와 안정적인 ID | 표, 제목, 비고와 적용 조건을 보존하는 논리 단위 분할 |
| `src/ingestion/indexing.py` | provider 기반 색인 스냅샷 생성과 메모리 캐시 | 실제 임베딩 provider와 갱신 정책 |
| `src/infrastructure/embeddings.py` | provider 경계, 데모 해시 임베딩, LangChain 연결 | 사용할 모델과 설정 |
| `src/infrastructure/stores.py` | 검증 가능한 로컬 JSON 색인 저장/읽기 | 실제 DB/벡터 저장소 |
| `src/pipeline.py` | 주입받은 팀 함수를 연결하는 공통 호출 흐름 | 지역 해석, 질문 변환, 검색, 답변 생성과 장소 조회 |
| `src/observability/records.py` | 실행 원본 기록 | 운영 저장 위치와 보존 정책, Langfuse 연결 |
| `src/evaluation/runner.py` | 같은 공통 흐름으로 평가 사례 실행 | Ragas, Hit@5, 사람 채점과 최종 비교 |
| `src/config.py`, `src/runtime.py` | 설정 읽기와 함수 연결 | 실제 서비스의 설정 및 자원 생성 |
| `src/demo.py`, `scripts/demo.py` | 외부 API 없는 합성 흐름 확인 | 실제 서비스 성능 평가로 대체하지 않음 |
| `scripts/index.py`, `scripts/evaluate.py` | 명시적인 입력/출력 파일을 받는 CLI | 실제 자료와 검증용 사례 경로 |

## 구현 경계와 검증

이 인계본에는 실제 팀 A/B/C 검색, 질문 변환 모델, 답변 LLM, 지도 UI, 장소 DB, Ragas와 Langfuse 연동이 포함되지 않는다. Streamlit이나 HTTP 서버도 이 공통 기반의 실행 조건이 아니다. 데모의 해시 임베딩과 원문 인용 생성기는 연결 확인용이며 최종 20문항 평가나 HTML/JSON 성능 비교 결과로 사용하지 않는다.

Python 3.13.14 환경에서 확인한 결과는 다음과 같다.

- 직접 질문 실행기 검사를 포함한 전체 테스트 183개가 `pytest tests`에서 통과했다. `src`, `scripts`, `app.py`의 `compileall`도 통과했다. 기존 `SourceDocument`의 AST가 변경 전과 일치함을 확인했다.
- 실제 데모 CLI에서 출처 목록 4건과 첨부 21건을 읽고, 합성 문서 3개의 청크와 실행 JSON 3개를 생성했다. 결과는 `answered`, `needs_clarification`, `insufficient_evidence`로 구분됐다.
- 색인 CLI의 기본 64차원 결과를 평가 CLI가 읽는 흐름, 연결 함수 오류의 기록과 종료 코드 1, 재실행 시 기존 결과를 덮어쓰지 않는 동작을 통합 테스트로 확인했다.
- 직접 질문 CLI에서는 구 변경에 따른 답변/출처, 근거 부족, 지역 재질문, 빈 입력과 종료, 원본 기록 보존을 확인했다.

실제 외부 API, DB와 팀 모듈 연결은 검증하지 않았다. 위 결과는 로컬 공통 흐름과 오류 처리의 검증이며, 실제 분리배출 답변 정확도나 HTML/JSON 성능 비교 결과가 아니다.

코드 변경과 로컬 실행 결과를 원격 배포나 원격 PR 완료로 해석하지 않는다. 팀 저장소로 공유할 때는 실제 변경과 검증 결과를 기준으로 별도 PR을 작성한다.
