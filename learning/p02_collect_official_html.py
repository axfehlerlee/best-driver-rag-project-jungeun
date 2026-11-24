"""P02 서대문구 생활쓰레기 안내 수집과 로컬 Selenium 저장."""

import argparse
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from os import X_OK, access
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from learning.p02_capture_html import capture_html

SOURCE_URL = "https://www.sdm.go.kr/civil/type/household.do"
ROBOTS_URL = "https://www.sdm.go.kr/robots.txt"
ROBOTS_SHA256 = "d5fe01249d3ee909af13f3e02a4726e3c1f9fc44c36dca0b32262353511672da"
COPYRIGHT_URL = "https://www.sdm.go.kr/user/copyright.do"
LICENSE_URL = "https://www.kogl.or.kr/info/licenseType1.do"
USER_AGENT = "TeamB-Recycling-RAG/1.0"
SELECTOR = "table caption"


class RejectRedirect(HTTPRedirectHandler):
    """검토된 주소에서 한 번만 요청."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(
            req.full_url, code, "리다이렉트 대상은 재검토 필요", headers, fp
        )


class PageText(HTMLParser):
    """공공누리 표시 확인에 사용할 DOM 텍스트."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _fetch(url: str, content_type: str, max_bytes: int) -> tuple[bytes, str | None]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with build_opener(RejectRedirect()).open(request, timeout=15) as response:
        if (
            response.status != 200
            or response.headers.get_content_type() != content_type
        ):
            raise ValueError(f"예상한 HTTP 200 {content_type} 응답이 아닙니다.")
        payload = response.read(max_bytes + 1)
        if not payload or len(payload) > max_bytes:
            raise ValueError("응답이 비어 있거나 크기 한도를 초과했습니다.")
        return payload, response.headers.get("Last-Modified")


def _confirm_license(html: str) -> None:
    parser = PageText()
    parser.feed(html)
    parser.close()
    text = " ".join(" ".join(parser.parts).split())
    if not re.search(
        r"서대문구청이\(가\)\s*창작한.{0,12}생활쓰레기\s*배출.{0,12}"
        r"저작물은\s*공공누리.{0,8}제\s*1\s*유형\s*:\s*출처\s*표시",
        text,
    ):
        raise ValueError(
            "생활쓰레기 배출 본문의 공공누리 제1유형 표시를 확인하지 못했습니다."
        )


def collect(output_dir: Path, driver_path: Path) -> Path:
    """접근 조건 확인 후 HTML과 수집 기록 저장. 기존 결과를 보호한다."""
    from selenium.common.exceptions import WebDriverException

    output_dir.mkdir(parents=True, exist_ok=False)
    manifest_path = output_dir / "manifest.json"
    manifest = {
        "document_title": "생활쓰레기 배출",
        "publisher": "서대문구청",
        "district": "서대문구",
        "source_url": SOURCE_URL,
        "robots_url": ROBOTS_URL,
        "copyright_url": COPYRIGHT_URL,
        "usage_status": "index_and_model_use_unreviewed",
    }
    try:
        robots, _ = _fetch(ROBOTS_URL, "text/plain", 100_000)
        manifest["robots_sha256"] = sha256(robots).hexdigest()
        manifest["robots_checked_at"] = datetime.now(timezone.utc).isoformat()
        if manifest["robots_sha256"] != ROBOTS_SHA256:
            raise ValueError(
                "robots.txt가 검토본과 달라 접근 조건 재확인이 필요합니다."
            )

        # 사이트에는 본문 GET 한 번. 리소스 렌더링은 로컬 브라우저에서 수행.
        manifest["requested_at"] = datetime.now(timezone.utc).isoformat()
        source, last_modified = _fetch(SOURCE_URL, "text/html", 2_000_000)
        manifest["http_last_modified"] = last_modified
        manifest["response_sha256"] = sha256(source).hexdigest()
        with TemporaryDirectory(prefix="team-b-p02-") as tmp:
            source_path = Path(tmp) / "source.html"
            source_path.write_bytes(source)
            html = capture_html(source_path, SELECTOR, driver_path)
        _confirm_license(html)

        payload = html.encode("utf-8")
        pending_path = output_dir / ".rendered.html.tmp"
        pending_path.write_bytes(payload)
        pending_path.rename(output_dir / "rendered.html")
        manifest.update(
            collected_at=datetime.now(timezone.utc).isoformat(),
            collection_status="saved",
            license="KOGL Type 1",
            license_url=LICENSE_URL,
            license_scope="생활쓰레기 배출 본문",
            artifact_type="local_rendered_html",
            artifact="rendered.html",
            rendered_sha256=sha256(payload).hexdigest(),
        )
    except (OSError, ValueError, WebDriverException) as error:
        manifest.update(collection_status="failed", error_type=type(error).__name__)
        raise
    finally:
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="새 로컬 결과 폴더")
    parser.add_argument(
        "--driver", type=Path, required=True, help="ChromeDriver 실행 파일"
    )
    args = parser.parse_args()
    if not args.driver.is_file() or not access(args.driver, X_OK):
        parser.error("실행 가능한 로컬 ChromeDriver 파일을 지정하세요.")
    if args.output_dir.exists() or args.output_dir.is_symlink():
        parser.error("새 출력 폴더를 지정하세요.")

    from selenium.common.exceptions import WebDriverException

    try:
        manifest_path = collect(args.output_dir, args.driver)
    except WebDriverException:
        parser.exit(1, "Selenium에서 본문 표를 확인하지 못했습니다.\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"수집 실패 ({error})\n")
    print("수집 기록", manifest_path.resolve())


if __name__ == "__main__":
    main()
