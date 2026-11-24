"""합성 질문 CLI의 입력, 지역 전환과 실행 기록을 외부 API 없이 확인한다."""

import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_chat(output, input_text, *arguments):
    return subprocess.run(
        [sys.executable, "-m", "scripts.chat", "--output-dir", str(output), *arguments],
        input=input_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=30,
    )


def read_runs(output):
    return [json.loads(path.read_text(encoding="utf-8")) for path in (output / "runs").glob("*.json")]


def test_chat_answers_each_question_with_the_current_district(tmp_path):
    output = tmp_path / "interactive"
    process = run_chat(
        output,
        "\n품목알파\n없는품목오메가\n/구 송파구\n품목알파\n/종료\n",
        "--demo", "--district", "서대문구",
    )
    assert process.returncode == 0, process.stdout + process.stderr
    assert "합성" in process.stdout
    records = read_runs(output)
    assert len(records) == 3  # 공백과 명령은 질문 실행 기록으로 만들지 않는다.
    assert len({record["request_id"] for record in records}) == 3
    assert len({record["run_id"] for record in records}) == 3
    assert all(record["run_kind"] == "demo" for record in records)
    by_request = {(record["request"]["question"], record["request"]["district"]): record for record in records}
    for district, expected_condition, document_id in (
        ("서대문구", "조건엑스", "demo-seodaemun"),
        ("송파구", "조건와이", "demo-songpa"),
    ):
        record = by_request["품목알파", district]
        response = record["response"]
        assert response["status"] == "answered"
        assert expected_condition in response["answer"]
        assert {citation["document_id"] for citation in response["citations"]} == {document_id}
        assert {citation["chunk_id"] for citation in response["citations"]} <= set(record["model_input_chunk_ids"])
    unknown = by_request["없는품목오메가", "서대문구"]["response"]
    assert unknown["status"] == "insufficient_evidence"
    assert unknown["citations"] == []


def test_missing_initial_district_asks_for_clarification_and_eof_exits(tmp_path):
    output = tmp_path / "no-district"
    # 첫 빈 줄은 지역 미지정, 다음 줄은 질문이다. 종료 명령 없이 EOF를 전달한다.
    process = run_chat(output, "\n품목알파\n", "--demo")
    assert process.returncode == 0, process.stdout + process.stderr
    records = read_runs(output)
    assert len(records) == 1
    record = records[0]
    assert record["request"]["district"] is None
    assert record["response"]["status"] == "needs_clarification"
    assert record["response"]["answer"].strip()
    assert record["response"]["citations"] == []
    assert record["model_input_chunk_ids"] == []


def test_existing_output_directory_is_rejected_without_changing_files(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    sentinel = output / "keep.json"
    sentinel.write_bytes(b'{"existing":true}\n')
    original = sentinel.read_bytes()
    process = run_chat(output, "/종료\n", "--demo", "--district", "서대문구")
    assert process.returncode != 0
    assert sentinel.read_bytes() == original
    assert list(output.iterdir()) == [sentinel]


def test_demo_mode_must_be_explicit_before_creating_output(tmp_path):
    output = tmp_path / "missing-mode"
    process = run_chat(output, "", "--district", "서대문구")
    assert process.returncode == 2
    assert not output.exists()
