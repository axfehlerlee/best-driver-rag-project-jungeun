import json
from pathlib import Path

from src.retrieval.spots import extract_items, infer_collection_types, parse_places

FIXTURE = Path(__file__).parent.parent / "fixtures" / "getspot_yeonhui_sample.json"


def load_sample() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_extract_items_reads_nested_list():
    # 응답은 response → body → items → item 안에 있다.
    assert len(extract_items(load_sample())) == 5


def test_extract_items_handles_empty_result():
    # 결과 없음(NODATA)이면 items가 빈 문자열로 올 수 있다 → 빈 목록.
    raw = {"response": {"header": {"resultCode": "03"}, "body": {"items": ""}}}
    assert extract_items(raw) == []


def test_infer_collection_types_from_spot_name():
    # 표기가 달라도(·, 공백) 같은 품목을 찾는다.
    assert sorted(infer_collection_types("폐형광등·폐건전지 수거함")) == ["폐건전지", "폐형광등"]
    assert sorted(infer_collection_types("폐형광등 폐건전지 수거함")) == ["폐건전지", "폐형광등"]


def test_infer_collection_types_returns_empty_for_unknown_name():
    # 품목을 알 수 없는 장소명은 빈 목록 (받는다고 단정하지 않는다).
    assert infer_collection_types("재활용정거장") == []


def test_parse_places_drops_other_city_with_same_dong_name():
    # 인천 연희동은 빼고 서대문구 장소만 남긴다.
    places = parse_places(load_sample(), "서대문구")

    assert len(places) == 4
    assert all("서대문구" in place.address for place in places)


def test_parse_places_keeps_unknown_coordinates_as_none():
    # getSpot 응답에 좌표가 없으므로 추측하지 않고 None으로 둔다.
    place = parse_places(load_sample(), "서대문구")[0]

    assert place.name == "폐형광등·폐건전지 수거함"
    assert place.latitude is None and place.longitude is None
    assert sorted(place.collection_types) == ["폐건전지", "폐형광등"]
