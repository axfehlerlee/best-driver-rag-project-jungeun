"""사용자가 직접 질문을 입력하는 합성 데모. 실제 분리배출 안내가 아니다."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

from src.config import load_settings
from src.contracts import PipelineRequest
from src.demo import create_demo_pipeline
from src.infrastructure.embeddings import DemoHashEmbeddings
from src.infrastructure.stores import save_index
from src.ingestion.chunking import chunk_documents
from src.ingestion.indexing import build_index
from src.ingestion.loaders import load_source_documents


class _DisplayText(HTMLParser):
    """터미널 표시만 읽기 쉽게 바꾼다. 원본 답변과 실행 JSON은 그대로 보존한다."""

    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def _read_district() -> str | None:
    while True:
        value = input("구 (서대문구 / 송파구, Enter: 미지정): ").strip()
        if value in {"", "서대문구", "송파구"}:
            return value or None
        print("서대문구, 송파구 또는 빈칸을 입력하세요.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", required=True, help="합성 자료 사용을 명시")
    parser.add_argument("--district", choices=("서대문구", "송파구"))
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (args.output_dir or root / "results/local" / f"chat-demo-{uuid4().hex}").resolve()
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("기존 실행 결과를 덮어쓸 수 없습니다. 새 --output-dir를 지정하세요.")
    settings = load_settings(root / "configs/demo.json", project_root=root)
    settings.index_path = output / "index.json"
    settings.runs_path = output / "runs"
    documents = load_source_documents(root / "tests/fixtures/handoff_documents.json")
    chunks = chunk_documents(documents, max_characters=settings.max_document_characters)
    save_index(build_index(chunks, DemoHashEmbeddings(settings.demo_dimensions)), settings.index_path)
    pipeline = create_demo_pipeline(settings)
    print("합성 데모: 실제 분리배출 안내나 LLM 답변이 아닙니다. 외부 API를 호출하지 않습니다.")
    print("예시 질문: 품목알파 / 공통시험품목 / 없는품목오메가")
    print("각 질문은 독립 처리합니다. 이전 대화를 기억하거나 지역을 문장에서 추론하지 않습니다.")
    print("구 변경: /구 송파구 또는 /구 | 종료: /종료")
    print(f"실행 기록: {settings.runs_path}")
    try:
        district = args.district or _read_district()
        while True:
            question = input(f"\n[{district or '구 미지정'}] 질문: ").strip()
            if question.lower() in {"/종료", "/exit", "/quit"}:
                break
            if not question:
                continue
            if question == "/구":
                district = _read_district()
                continue
            if question.startswith("/구 "):
                value = question[3:].strip()
                if value in {"서대문구", "송파구"}:
                    district = value
                else:
                    print("지원하는 구는 서대문구와 송파구입니다.")
                continue
            record = pipeline.run(PipelineRequest(question=question, district=district))
            response = record.response
            display = _DisplayText()
            display.feed(response.answer)
            display.close()
            print(f"상태: {response.status}")
            print("\n".join(display.parts))
            for citation in response.citations:
                print(f"출처: {citation.title} | {citation.source_url}")
            if response.error:
                print(f"오류: {response.error}")
            print(f"실행 ID: {record.run_id}")
    except (EOFError, KeyboardInterrupt):
        pass
    print("\n질문 테스트를 종료했습니다.")


if __name__ == "__main__":
    main()
