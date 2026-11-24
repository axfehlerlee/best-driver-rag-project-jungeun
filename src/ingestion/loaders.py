"""sources.json의 문서 목록과 조례/첨부 관계를 읽는다.

담당: 양석호
SourceDocument는 유지하고, 사용자가 지정한 출처 목록부터 읽기로 했다.
이 목록에는 본문과 내부 버전이 없으므로 SourceDocument를 임의로 생성하지 않는다.
목록의 한글 키를 아래 입력 모델에 연결하며, 원문 다운로드와 전처리는 수행하지 않는다.
"""

import json
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Annotated, Self
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)


# 번호의 선행 0, 제목과 URL의 원래 표기를 보존한다. 숫자를 문자열로 추정 변환하지 않는다.
_NonBlankString = Annotated[
    str, StringConstraints(strict=True, min_length=1, pattern=r"\S")
]


class SourceManifestError(ValueError):
    """파일 내용이 지원하는 출처 목록 형식과 맞지 않을 때 발생한다."""


def _validate_source_url(value: str) -> str:
    """주소를 요청하거나 정규화하지 않고 HTTP(S) 주소의 형태만 검사한다."""
    if any(character.isspace() or ord(character) < 32 for character in value):
        raise ValueError("출처 URL에는 공백이나 제어 문자를 넣을 수 없습니다.")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        # 잘못된 포트 번호도 urlsplit 결과를 사용하는 시점에 확인한다.
        _ = parsed.port
    except ValueError as error:
        raise ValueError("유효한 HTTP(S) 출처 URL이 필요합니다.") from error
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError("호스트가 있는 HTTP(S) 출처 URL이 필요합니다.")
    return value


class AttachmentLink(BaseModel):
    """한 조례/시행규칙의 별표_링크 항목. 부모는 이를 담은 SourceManifestEntry다."""

    # 전처리 결과의 다른 구조를 잘못 읽거나 새 필드를 조용히 버리지 않도록 오류로 알린다.
    model_config = ConfigDict(extra="forbid", strict=True)

    # 목록상의 번호다. 실제 별표 제N호나 내부 document_id로 해석하지 않는다.
    number: _NonBlankString = Field(alias="번호")
    title: _NonBlankString = Field(alias="제목")
    source_url: _NonBlankString = Field(alias="파일_URL")

    _check_source_url = field_validator("source_url")(_validate_source_url)


class SourceManifestEntry(BaseModel):
    """출처 목록 한 건과 그 문서에 포함된 첨부 링크. 추출된 본문 문서와 구분한다."""

    model_config = ConfigDict(extra="forbid", strict=True)

    district: _NonBlankString = Field(alias="구")
    title: _NonBlankString = Field(alias="자치법규명")
    # 수집처의 일련번호다. 개정 후 유지되는 내부 문서 ID나 버전이라고 가정하지 않는다.
    ordinance_serial: _NonBlankString = Field(alias="일련번호")
    effective_date: date = Field(alias="시행일")
    source_url: _NonBlankString = Field(alias="원문_URL")
    # 목록에 기재된 상대 경로만 보존한다. 파일 존재나 보관 완료를 의미하지 않으며
    # SourceDocument.raw_path로 옮길 때 실제 프로젝트 내 위치를 별도로 확인해야 한다.
    body_file: _NonBlankString = Field(alias="본문_파일")
    # 부모별로 목록을 유지하므로 다른 조례에서 같은 첨부 번호가 나와도 섞이지 않는다.
    # 삭제/별지/서식도 원래 순서대로 보존하고, 검색 대상 여부는 이 로더에서 결정하지 않는다.
    attachments: list[AttachmentLink] = Field(alias="별표_링크")
    attachment_status: _NonBlankString = Field(alias="별표_상태")

    _check_source_url = field_validator("source_url")(_validate_source_url)

    @field_validator("effective_date", mode="before")
    @classmethod
    def _parse_effective_date(cls, value: object) -> date:
        # YYYYMMDD를 명시적으로 읽는다. 숫자형 날짜를 타임스탬프로 해석하지 않는다.
        if (
            not isinstance(value, str)
            or len(value) != 8
            or not value.isascii()
            or not value.isdecimal()
        ):
            raise ValueError("시행일은 YYYYMMDD 형식의 8자리 문자열이어야 합니다.")
        try:
            return date(int(value[:4]), int(value[4:6]), int(value[6:]))
        except ValueError as error:
            raise ValueError("시행일은 실제 달력에 존재하는 날짜여야 합니다.") from error

    @field_validator("body_file")
    @classmethod
    def _validate_body_file(cls, value: str) -> str:
        relative_path = PurePosixPath(value.replace("\\", "/"))
        if (
            not relative_path.parts
            or relative_path.is_absolute()
            or PureWindowsPath(value).anchor
            or ":" in value
            or ".." in relative_path.parts
            or "\0" in value
        ):
            raise ValueError("본문_파일은 상위 경로 이동이 없는 상대 파일 경로여야 합니다.")
        # 여기서 원본 파일을 열거나 다운로드하지 않는다. 선언된 경로 표기도 바꾸지 않는다.
        return value

    @model_validator(mode="after")
    def _check_attachment_numbers(self) -> Self:
        seen: set[str] = set()
        for index, attachment in enumerate(self.attachments):
            if attachment.number in seen:
                raise ValueError(
                    f"별표_링크[{index}].번호 {attachment.number!r}가 같은 부모 안에서 중복됩니다."
                )
            seen.add(attachment.number)
        return self


_SOURCE_MANIFEST = TypeAdapter(list[SourceManifestEntry])


def _unique_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """JSON 중복 키를 마지막 값으로 덮어써 출처 정보를 잃지 않게 한다."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SourceManifestError(f"중복 JSON 필드 {key!r}가 있습니다.")
        result[key] = value
    return result


def load_source_manifest(path: str | Path) -> list[SourceManifestEntry]:
    """UTF-8 출처 목록을 읽고 문서 순서와 부모별 첨부 관계를 보존해 반환한다.

    UTF-8 BOM도 허용한다. 형식 오류는 파일 경로와 문제 위치를 포함한
    SourceManifestError로 알리며, 파일 접근 오류는 FileNotFoundError 등으로 전달한다.
    입력 전체가 유효할 때만 반환하고, 본문/버전/저장 경로를 만들어 채우지 않는다.
    """
    manifest_path = Path(path)
    try:
        raw_text = manifest_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise SourceManifestError(f"{manifest_path}: UTF-8 JSON 파일이 필요합니다.") from error

    try:
        payload = json.loads(raw_text, object_pairs_hook=_unique_json_keys)
    except json.JSONDecodeError as error:
        raise SourceManifestError(
            f"{manifest_path}: JSON 문법 오류 ({error.lineno}행 {error.colno}열): {error.msg}"
        ) from error
    except SourceManifestError as error:
        raise SourceManifestError(f"{manifest_path}: {error}") from error

    try:
        entries = _SOURCE_MANIFEST.validate_python(payload, strict=True)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(map(str, item['loc'])) or '최상위 목록'}: {item['msg']}"
            for item in error.errors(include_input=False, include_url=False)
        )
        raise SourceManifestError(f"{manifest_path}: 출처 목록 형식 오류: {details}") from error

    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if entry.ordinance_serial in seen:
            raise SourceManifestError(
                f"{manifest_path}: [{index}].일련번호 {entry.ordinance_serial!r}가 중복됩니다."
            )
        seen.add(entry.ordinance_serial)
    return entries
