from src.retrieval.regions import resolve_region


def test_resolve_region_returns_district_for_supported_dong():
    result = resolve_region("연희동 페트병 언제 버려요?")
    assert result == {"status": "ok", "district": "서대문구", "dong": "연희동"}


def test_resolve_region_returns_district_for_songpa_dong():
    result = resolve_region("잠실동 폐건전지 언제 버려요?")
    assert result == {"status": "ok", "district": "송파구", "dong": "잠실동"}


def test_resolve_region_does_not_guess_shared_dong_name():
    result = resolve_region("신사동 쓰레기 언제?")
    assert result["status"] == "ambiguous"
    assert result["candidate_districts"] == ["강남구", "관악구"]


def test_resolve_region_marks_unsupported_district():
    result = resolve_region("역삼동 쓰레기 언제?")
    assert result == {"status": "unsupported", "district": "강남구", "dong": "역삼동"}


def test_resolve_region_returns_no_dong_when_question_has_no_dong():
    assert resolve_region("페트병 언제 버려요?") == {"status": "no_dong"}
