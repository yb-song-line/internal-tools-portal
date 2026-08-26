# Internal Tools Portal

팀 공용 웹 도구를 한곳에 모아 제공하는 설정 기반 포털입니다. 기본 배포는 사내 GitHub Enterprise Pages를 사용하며 `git.linecorp.com` 로그인 이후에만 접근할 수 있습니다.

## 도구 추가

`config/tools.json`의 `tools` 배열에 항목을 추가합니다. 사내 GitHub Pages, Render, 사내 서비스 등 `https://` URL이면 모두 등록할 수 있습니다.

```json
{
  "id": "sample-tool",
  "name": "샘플 도구",
  "description": "도구 설명",
  "url": "https://example.com/",
  "sourceUrl": "https://git.linecorp.com/example/sample-tool",
  "category": "업무 자동화",
  "icon": "🧰",
  "tags": ["태그1", "태그2"],
  "processing": "브라우저 내부 처리",
  "access": "external-public",
  "order": 30,
  "enabled": true
}
```

`access` 값:

- `portal-protected`: 포털 내부 경로에 있어 포털 인증 적용
- `enterprise-protected`: 사내 GitHub Enterprise 로그인 적용
- `external-public`: 외부 공개 URL이므로 포털을 통하지 않고도 직접 접근 가능

## 사내 GitHub Pages 배포

저장소는 `https://git.linecorp.com/yb-song/internal-tools-portal`에 있으며, Pages는 `main` 브랜치의 루트에서 배포합니다.

Pages 주소는 `https://git.linecorp.com/pages/yb-song/internal-tools-portal/`입니다. 미로그인 사용자는 사내 Git 로그인 화면으로 이동하므로 공유 비밀번호를 별도로 저장하지 않습니다.

## 로컬 실행

```bash
PORTAL_USERNAME=team \
PORTAL_PASSWORD='10자 이상의 비밀번호' \
SESSION_SECRET='32자 이상의 임의 문자열' \
python3 server.py
```

브라우저에서 <http://127.0.0.1:8787>을 엽니다.

로컬 UI 개발 중에만 다음과 같이 인증을 생략할 수 있습니다.

```bash
PORTAL_DEV_BYPASS=1 python3 server.py
```

## Python 서버 배포

`server.py`는 공유 비밀번호가 꼭 필요한 별도 서버 환경에서 사용할 수 있습니다. `PORTAL_PASSWORD`와 `SESSION_SECRET`을 서버 환경변수로 설정합니다.

Render는 사내 GitHub Enterprise 저장소를 직접 연결할 수 없으므로 현재 포털 배포에는 사용하지 않습니다.

## 인증 범위

사내 Pages 배포는 GitHub Enterprise 로그인을 요구합니다. 카드가 가리키는 외부 공개 URL 자체는 별도로 보호되지 않으므로 민감정보를 입력하지 않아야 합니다. Python 서버 배포에서는 포털 로그인과 `/api/tools`가 공유 비밀번호로 보호됩니다.
