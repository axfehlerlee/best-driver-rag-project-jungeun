# Python·Next.js 커버리지와 의존성 관리

[팀 개발 환경](TEAM-SETUP.md)의 폴더 구조를 전제로 합니다. 통합 담당자가 설정 파일을 관리하고, 각 모듈 담당자가 자신의 테스트와 의존성 변경을 검토합니다. 설정 파일은 저장소에 포함되어 있습니다. 아래에서 파일을 열어 확인하고, 앱을 만들 때 각 언어의 테스트 의존성과 실행 명령을 연결합니다.

## 1. 언어별로 보고서 만들기

| 대상 | 테스트 도구 | 저장소 루트 기준 결과 파일 | Codecov 플래그 |
| --- | --- | --- | --- |
| Python 백엔드 | pytest + pytest-cov | `backend/coverage.xml` | `backend` |
| Next.js 프론트엔드 | Vitest + V8 coverage | `frontend/coverage/lcov.info` | `frontend` |

**Python.** 루트의 `uv.lock`에서 개발 의존성까지 설치합니다. 저장소 루트의 [Python 커버리지 설정](../.coveragerc)을 사용합니다. `source = .`로 소스 경로에 `backend/` 접두사를 보존하고, 보고서는 백엔드 제품 코드로 제한합니다.

저장소 루트에서 실행합니다. 첫 테스트는 고정 검색기가 빈 결과를 반환할 때 질의 처리기가 `insufficient_evidence`를 반환하는 경우로 시작할 수 있습니다.

~~~sh
uv sync --locked
uv run --locked python -m pytest backend/tests --cov --cov-config=.coveragerc --cov-report=xml:backend/coverage.xml
~~~

**Next.js.** `frontend/`에서 아래 명령을 실행합니다. 테스트 러너와 V8 도구는 같은 릴리스로 설치하고 `package.json`과 `package-lock.json`을 함께 기록합니다. 첫 테스트로 `src/lib/chat.ts`의 추가 질문 재전송 로직을 검증하면 브라우저나 실서버가 필요 없습니다.

~~~sh
npm install -D --save-exact vitest@latest @vitest/coverage-v8@latest
npm pkg set 'scripts.test:coverage=vitest run --coverage'
~~~

[프론트엔드 Vitest 설정](../frontend/vitest.config.ts)이 LCOV를 생성합니다.

로컬에서는 `frontend/`에서 `npm run test:coverage`를 실행합니다. 첫 업로드 전 XML의 `filename`이 `backend/`로 시작하는지, LCOV의 `SF:` 경로가 `src/`로 시작하는지 확인합니다. 두 보고서의 커버리지는 제품 코드의 테스트 실행 범위입니다. 구별 정확도와 인용 품질은 [로드맵의 평가표](../ROADMAP.md)에서 별도로 측정합니다.

## 2. Codecov 연결과 GitHub Actions

저장소 관리자가 Codecov에서 해당 GitHub 저장소를 활성화하고 저장소 전용 업로드 토큰을 GitHub의 **Settings → Secrets and variables → Actions**에 `CODECOV_TOKEN`으로 등록합니다. 아래 워크플로는 일반 팀 PR과 `main`에서 두 보고서를 올리고, 포크 PR·Dependabot PR에서는 인증 정보 없이 두 테스트만 실행합니다. 팀 PR이나 `main`에서 업로드가 실패하면 해당 작업도 실패합니다. [Codecov 공식 액션과 지원 입력](https://github.com/codecov/codecov-action/tree/v7.1.1)

[커버리지 워크플로](../.github/workflows/coverage.yml)는 Python 환경을 항상 `uv sync --locked`로 재현합니다. 백엔드 Python 파일이 생기면 테스트와 업로드도 실행합니다. Next.js는 `frontend/package.json`이 생기면 테스트를 시작합니다.

[Codecov 설정](../codecov.yml)은 저장소 루트에 있습니다. LCOV 경로를 Git 경로로 맞추고 각 플래그가 담당하는 디렉터리를 지정합니다. 팀이 아직 합의하지 않은 최소 커버리지 수치는 지정하지 않았습니다.

**연결 확인 기준.** 테스트가 있는 첫 `main` 실행으로 비교 기준을 만듭니다. 이후 팀 PR에서 두 작업이 성공하고 Codecov의 같은 커밋에 `backend`·`frontend` 플래그가 모두 표시되는지 확인합니다. 각 플래그에서 변경 파일 하나를 열어 줄별 커버리지까지 확인합니다. [액션 릴리스](https://github.com/codecov/codecov-action/releases/tag/v7.1.1) · [경로 보정](https://docs.codecov.com/docs/fixing-paths)

## 3. GitHub Dependabot

[Dependabot 설정](../.github/dependabot.yml)에 주간 버전 확인을 설정했습니다. Python의 `uv` 생태계와 잠금 파일 위치는 저장소 루트(`/`), npm 잠금 파일 위치는 `/frontend`입니다. 두 Dockerfile의 기반 이미지와 저장소 루트에서 관리하는 GitHub Actions도 갱신 대상입니다. 현재 Compose는 로컬 Dockerfile을 빌드하므로 외부 이미지는 두 Dockerfile에서 추적합니다. [GitHub 지원 생태계](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories) · [Dependabot 설정 옵션](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)

**활성화와 첫 확인.** 기본 브랜치에 매니페스트·잠금 파일과 위 설정을 반영하면 버전 갱신 작업을 예약할 수 있습니다. 보안 취약점 수정 PR도 받을 때는 저장소 설정에서 Dependency graph, Dependabot alerts, Dependabot security updates를 활성화합니다. GitHub의 Dependabot 작업 기록에서 각 경로가 인식됐는지 확인합니다. 최신 상태라 PR이 생기지 않은 경우에도 작업 기록에서 확인할 수 있습니다.

기반 이미지 버전 변경 PR은 루트의 `.python-version` 또는 CI의 `node-version`과 함께 검토합니다. Dependabot은 Docker 이미지 태그를 올려도 CI 입력에 적은 런타임 문자열까지 동기화하지는 않습니다. Python 패키지 변경 때는 `pyproject.toml`과 `uv.lock`을 확인하고 npm 변경 때는 잠금 파일까지 함께 검토합니다.
