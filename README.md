# 업무 포털

팀 공용 웹 도구와 공개 정보 기반 참고 자료를 한곳에 모아 제공하는 설정 기반 포털입니다. 기본 배포는 사내 GitHub Enterprise Pages를 사용하며 `git.linecorp.com` 로그인 이후에만 접근할 수 있습니다.

## 도구 추가

`config/tools.json`의 `tools` 배열에 항목을 추가합니다. 사내 GitHub Pages, Render, 사내 서비스 등 `https://` URL이면 모두 등록할 수 있습니다.

```json
{
  "id": "sample-tool",
  "name": "샘플 도구",
  "description": "도구 설명",
  "url": "https://example.com/",
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

## 인사이트 자료 추가

`config/tools.json`의 `references` 배열에 공개 HTML 보고서나 분석 자료를 추가합니다.

```json
{
  "id": "sample-public-report",
  "name": "공개 동향 보고서",
  "description": "외부 공개 자료를 시각화한 HTML 보고서입니다.",
  "url": "https://example.com/report.html",
  "category": "시장 동향",
  "icon": "▤",
  "tags": ["공개 자료", "HTML"],
  "basis": "외부 공개 정보 기반",
  "access": "external-public",
  "order": 10,
  "enabled": true
}
```

인사이트 라이브러리에는 외부 공개 정보로만 작성되고 공개 배포가 허용된 자료를 등록합니다. 대외비, 개인정보, 미공개 실적, 계약 정보, API 키 또는 사내 전용 URL이 포함된 자료는 등록할 수 없습니다.

## 사내 GitHub Pages 배포

저장소는 `https://git.linecorp.com/yb-song/internal-tools-portal`에 있으며, Pages는 `main` 브랜치의 루트에서 배포합니다.

Pages 주소는 `https://git.linecorp.com/pages/yb-song/internal-tools-portal/`입니다. 미로그인 사용자는 사내 Git 로그인 화면으로 이동하므로 공유 비밀번호를 별도로 저장하지 않습니다.

외부 사용자는 `https://yb-song-line.github.io/internal-tools-portal/`에서 로그인 없이 이용할 수 있습니다. 외부 공개본에는 비밀번호, API 키, 사내 전용 URL, 개인정보 또는 미공개 업무 데이터를 추가하지 마세요.

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
