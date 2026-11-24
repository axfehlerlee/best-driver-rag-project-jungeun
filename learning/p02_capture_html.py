"""P02 실습용 로컬 HTML 렌더링 결과 저장."""

import argparse
from hashlib import sha256
from os import X_OK, access
from pathlib import Path


def capture_html(source: Path, selector: str, driver_path: Path) -> str:
    """로컬 HTML을 렌더링하고 UTF-8 선언으로 정리한 DOM을 읽는다."""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as ec
    from selenium.webdriver.support.ui import WebDriverWait

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-background-networking")
    # WebSocket의 직접 연결과 루프백 프록시 우회 차단
    options.add_argument("--proxy-server=http://127.0.0.1:9")
    options.add_argument("--proxy-bypass-list=<-loopback>")
    service = Service(executable_path=str(driver_path.resolve()))

    with webdriver.Chrome(service=service, options=options) as driver:
        # 로컬 파일에서 참조하는 HTTP·HTTPS 리소스 차단
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd(
            "Network.setBlockedURLs", {"urls": ["http://*", "https://*"]}
        )
        driver.set_page_load_timeout(15)
        driver.get(source.resolve().as_uri())
        WebDriverWait(driver, 10).until(
            ec.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        # 저장 바이트와 HTML의 문자 인코딩 선언 일치
        driver.execute_script("""
            const head = document.head;
            const charset = head.querySelector("meta[charset]")
                ?? document.createElement("meta");
            head.prepend(charset);
            charset.setAttribute("charset", "utf-8");
            for (const meta of document.querySelectorAll("meta[charset]")) {
                meta.setAttribute("charset", "utf-8");
            }
            for (const meta of document.querySelectorAll(
                'meta[http-equiv="content-type" i]'
            )) {
                meta.setAttribute("content", "text/html; charset=utf-8");
            }
        """)
        return driver.page_source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="입력할 로컬 HTML 파일")
    parser.add_argument("output", type=Path, help="새로 저장할 HTML 파일")
    parser.add_argument("--selector", default="table", help="기다릴 CSS 선택자")
    parser.add_argument(
        "--driver", type=Path, required=True, help="ChromeDriver 실행 파일"
    )
    args = parser.parse_args()

    if not args.source.is_file() or args.source.suffix.lower() not in {".html", ".htm"}:
        parser.error("입력은 존재하는 로컬 HTML 파일이어야 합니다.")
    if args.output.exists() or args.output.is_symlink():
        parser.error("새 출력 파일 이름을 지정하세요.")
    if not args.driver.is_file() or not access(args.driver, X_OK):
        parser.error("실행 가능한 로컬 ChromeDriver 파일을 지정하세요.")

    from selenium.common.exceptions import TimeoutException

    try:
        html = capture_html(args.source, args.selector, args.driver)
    except TimeoutException:
        parser.exit(1, f"HTML 로딩 또는 선택자 대기 시간 초과 ({args.selector})\n")
    payload = html.encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as file:
        file.write(payload)

    print("입력 파일", args.source.resolve())
    print("대기한 요소", args.selector)
    print("저장 파일", args.output.resolve())
    print("SHA-256", sha256(payload).hexdigest())


if __name__ == "__main__":
    main()
