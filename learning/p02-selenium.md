# P02 Selenium HTML 수집 실습

Python 3.13, Chrome, 설치된 Chrome과 호환되는 로컬 ChromeDriver를 사용한다. 저장소 루트에서 별도 Python 환경으로 실행한다.

```zsh
python3.13 -m venv .venv
.venv/bin/python -m pip install 'selenium==4.54.0'
```

## 로컬 HTML 저장

```zsh
.venv/bin/python -m learning.p02_capture_html ./input.html \
  ./results/local/p02-rendered.html --selector 'table' --driver /path/to/chromedriver
```

입력은 로컬 HTML 파일이다. 지정한 요소가 나타나면 UTF-8로 렌더링 결과를 저장하고 SHA-256을 출력한다. 출력에는 새 경로를 사용한다.

## 서대문구 공식 안내 수집

```zsh
.venv/bin/python -m learning.p02_collect_official_html \
  ./results/local/p02-seodaemun --driver /path/to/chromedriver
```

수집기는 서대문구의 ‘생활쓰레기 배출’ 페이지 한 건을 대상으로 한다. 검토한 `robots.txt`의 해시와 일치하면 본문을 한 번 요청한다. 받은 HTML을 로컬 Chrome에서 열고 공공누리 제1유형 표시를 확인한 뒤 새 폴더에 `rendered.html`과 `manifest.json`을 저장한다. 렌더링 결과와 HTTP 응답에는 각각의 SHA-256을 기록한다. robots 규칙이 바뀌면 대상 경로와 요청 간격을 다시 검토한다. 색인과 외부 모델 이용 상태는 `index_and_model_use_unreviewed`로 기록한다. [서대문구 공식 원문](https://www.sdm.go.kr/civil/type/household.do) · [robots.txt](https://www.sdm.go.kr/robots.txt)

검증 범위는 로컬 합성 HTML과 서대문구 안내 1건이다. 송파구 자동 수집은 대기 상태다.
