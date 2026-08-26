# Internal Tools Portal

팀 공용 웹 도구를 한곳에 모아 제공하는 설정 기반 포털입니다. 서버 측 로그인 이후에만 홈페이지와 도구 목록을 볼 수 있습니다.

## 도구 추가

`config/tools.json`의 `tools` 배열에 항목을 추가합니다. GitHub Pages, Render, 사내 서비스 등 `https://` URL이면 모두 등록할 수 있습니다.

```json
{
  "id": "sample-tool",
  "name": "샘플 도구",
  "description": "도구 설명",
  "url": "https://example.com/",
  "sourceUrl": "https://github.com/example/sample-tool",
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
- `external-public`: 외부 공개 URL이므로 포털을 통하지 않고도 직접 접근 가능

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

## Render 배포

저장소의 `render.yaml`을 Blueprint로 배포합니다. 배포 과정에서 `PORTAL_PASSWORD`를 입력하면 `SESSION_SECRET`은 Render가 자동 생성합니다.

무료 Web Service는 15분 동안 요청이 없으면 슬립되며 첫 접속 시 재기동 시간이 걸릴 수 있습니다.

## 인증 범위

포털 로그인은 포털 화면과 `/api/tools`를 보호합니다. 카드가 가리키는 외부 공개 URL 자체를 비공개로 바꾸지는 않습니다. 민감한 도구는 포털 내부 경로로 통합하거나 도구 자체에 별도 인증을 적용해야 합니다.
