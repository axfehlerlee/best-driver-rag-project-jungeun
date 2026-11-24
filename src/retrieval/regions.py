"""구와 동 이름 해석.

담당: 이명지
상태: 연습용 매핑표로 질문 속 동 이름을 자치구로 해석한다.
실제 행정동·법정동 매핑표와 공용 반환 규격은 사용하는 담당자와 합의한 뒤 교체한다.
"""

# 동 이름 → 그 동이 있는 구 목록 (연습용. 실제 행정동·법정동 매핑표로 교체 예정)
DONG_TO_DISTRICTS: dict[str, list[str]] = {
    "연희동": ["서대문구"],
    "잠실동": ["송파구"],
    "신사동": ["강남구", "관악구"],
    "역삼동": ["강남구"],
}

SUPPORTED_DISTRICTS: set[str] = {"서대문구", "송파구"}


def find_dong(question: str) -> str | None:
    """질문 속에서 매핑표에 있는 동 이름을 찾는다.

    Returns:
        찾은 동 이름. 질문에 매핑표의 동이 없으면 None.
    """
    for dong in DONG_TO_DISTRICTS:
        if dong in question:
            return dong
    return None


def resolve_region(question: str) -> dict:
    """질문 속 동 이름으로 자치구를 해석한다.

    모호하면 임의로 정하지 않는다(기획서 02). status는 내부 신호이며
    최종 응답 status 변환은 답변 생성 쪽에서 한다.

    Returns:
        status가 "ok" / "ambiguous" / "unsupported" / "no_dong" 중 하나인 dict.
    """
    dong = find_dong(question)
    if dong is None:
        return {"status": "no_dong"}

    districts = DONG_TO_DISTRICTS[dong]

    # 구가 여럿이면 하나를 고르지 않고 되묻는다. 지원 범위 검사보다 먼저 함.
    # 여러 구 검사를 먼저 하지 않으면 멋대로 신사동을 강남구로 찍어버림
    # (관악구일 가능성을 멋대로 차단함)
    if len(districts) > 1:
        return {"status": "ambiguous", "dong": dong, "candidate_districts": districts}

    district = districts[0]

    # 지원 범위인가?
    if district not in SUPPORTED_DISTRICTS:
        return {"status": "unsupported", "district": district, "dong": dong}

    return {"status": "ok", "district": district, "dong": dong}
