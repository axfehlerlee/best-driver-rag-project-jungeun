"""장소 저장과 조회.

담당: 이명지
상태: getSpot 응답을 공용 장소 형식(PlaceResult)으로 정리하는 단계.
DB 저장과 품목별 조회는 다음 단계에서 추가한다.

getSpot 응답에서 확인한 사실 (2026-11-24 실제 호출):
- 항목 필드는 spotNm(장소명), addrBase(주소), addrDtl(상세)뿐이다. 좌표와 품목 필드가 없다.
- addr(동 이름) 검색 결과에 다른 시의 같은 이름 동(예: 인천 연희동)이 섞인다.

흐름:
사용자 질문 "연희동 폐건전지 어디에 버리나요?" -> 답변 + 근처 수거함 목록을 보여주기
getSpot API는 그 장소 정보를 주는 역할.

getSpot API (날것)  →  [spots.py: 정리]  →  PlaceResult (팀 공용 형식)  →  승주 님 화면
"""

from src.contracts import PlaceResult

GETSPOT_SOURCE_URL = "https://www.data.go.kr/data/15156866/openapi.do"

# 장소명에서 찾을 품목 키워드. 같은 품목이 여러 표기로 와서(폐형광등·폐건전지 / 폐형광등 폐건전지)
# 장소명 전체가 아니라 키워드 포함 여부로 판단한다.
COLLECTION_KEYWORDS: tuple[str, ...] = (
    "폐건전지", "폐형광등", "의류", "폐의약품", "종량제봉투",
    "투명페트병", "종이팩", "아이스팩", "소형가전", "폐가전",
)


def extract_items(raw: dict) -> list[dict]:
    """getSpot 응답 JSON에서 장소 항목 목록을 꺼낸다.

    결과가 없으면 items가 비어 있거나 항목이 하나뿐이면 list가 아닐 수 있어 모두 list로 맞춘다.
    """
    items = raw.get("response", {}).get("body", {}).get("items") or {}
    item = items.get("item", []) if isinstance(items, dict) else items
    if isinstance(item, dict):
        return [item]
    return list(item)


def infer_collection_types(spot_name: str) -> list[str]:
    """장소명에서 받는 품목을 추론한다.

    예: "폐형광등·폐건전지 수거함" → ["폐건전지", "폐형광등"]
    품목 키워드가 없으면 빈 목록 (모르는 품목을 받는다고 단정하지 않는다).
    """

    # COLLECTION_KEYWORDS 중 spot_name 안에 들어 있는 것만 모아서 돌려주기
    found = []
    for keyword in COLLECTION_KEYWORDS:
        if keyword in spot_name:
            found.append(keyword)
    return found


def parse_places(raw: dict, district: str) -> list[PlaceResult]:
    """getSpot 응답을 district(예: "서대문구")에 있는 장소만 PlaceResult로 바꾼다.

    좌표는 응답에 없으므로 None으로 둔다 (추측해서 채우지 않는다).
    """
    places: list[PlaceResult] = []

    for item in extract_items(raw):
        address = item.get("addrBase", "")

        # 다른 시(인천 연희동 등)를 거르기
        # address에 district가 들어 있지 않으면 건너뛰기 (continue)
        if district not in address:
            continue

        # ②: PlaceResult 만들어서 places에 추가
        # name=장소명, address=주소, source_url=GETSPOT_SOURCE_URL,
        # collection_types=infer_collection_types(장소명),
        # place_id=f"getspot-{len(places) + 1}"  (임시 ID, DB 단계에서 바꿀 예정)

        spot_name = item.get("spotNm", "")

        places.append(PlaceResult(
            name=spot_name,
            address=address,
            source_url=GETSPOT_SOURCE_URL,
            collection_types=infer_collection_types(spot_name),
            place_id=f"getspot-{len(places) + 1}", # (임시 ID, DB 단계에서 바꿀 예정)
        ))
    return places
