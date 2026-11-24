"""Draft answers for the controlled, offline P04 fixed-evidence experiment."""

import re

from src.generation.answer import AnswerDraft, ConflictSide, GenerationInput


_COLOR_ROW = re.compile(r"[\w·]+ \w+색")


def draft_p04_answer(payload: GenerationInput) -> AnswerDraft:
    """Use only passages with a scope and format recognized by the P04 probe."""
    conditions = payload["conditions"]
    question = payload["original_question"]
    housing = conditions.get("housing_type")
    container = conditions.get("container_type")
    if isinstance(housing, str) and isinstance(container, str):
        if housing in question and container in question:
            heading = f'합성: {housing} "{container}" 기준'
            for index, evidence in enumerate(payload["evidence"]):
                title, _, body = evidence["text"].partition("\n")
                rows = body.split(", ")
                if title == heading and all(_COLOR_ROW.fullmatch(row) for row in rows):
                    return {
                        "status": "answered",
                        "message": f"{housing} {container} 기준은 {', '.join(rows)}입니다.",
                        "citation_indices": [index],
                    }

    item = conditions.get("item")
    if isinstance(item, str) and item and item in question:
        heading = f"합성: {item} 배출 기준"
        for index, evidence in enumerate(payload["evidence"]):
            title, _, body = evidence["text"].partition("\n")
            if title == heading and body.strip():
                return {
                    "status": "answered",
                    "message": body.strip(),
                    "citation_indices": [index],
                }

    dong = conditions.get("dong")
    if isinstance(dong, str) and isinstance(housing, str):
        if dong in question and housing in question:
            prefix = f"합성: {dong} {housing}의 일반·음식물 배출요일은 "
            sides: list[ConflictSide] = []
            schedules = set()
            for index, evidence in enumerate(payload["evidence"]):
                text = evidence["text"]
                if text.startswith(prefix) and (days := text.removeprefix(prefix).strip()):
                    sides.append({"evidence_index": index, "excerpt": text})
                    schedules.add(days)
            if len(schedules) > 1:
                return {"status": "source_conflict", "conflict_sides": sides}

    return {"status": "insufficient_evidence"}
