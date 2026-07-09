# 문서 작성 가이드

`docs_templates/`에 있는 템플릿을 복사해서 `docs/` 아래에 채워 넣으세요. `docs/` 안의 `.md` 파일만 색인(검색) 대상이 됩니다. 이 폴더(`docs_templates/`) 자체는 색인되지 않습니다.

## ⚠️ 시크릿 절대 금지

이 문서에는 비밀번호, API 키, SSH 개인키, 인증서, 토큰 등 어떤 시크릿도 절대 적지 마세요.
`credentials_location` 필드에는 "어디에 보관되어 있는지"만 적으세요.

예시:
- 올바름: `credentials_location: "1Password - Vault: Infra, Item: order-api-db"`
- 잘못됨: `credentials_location: "password123"`

이 규칙은 RAG로 색인되는 모든 문서에 예외 없이 적용됩니다. 색인된 내용은 AI 답변에 그대로 인용될 수 있습니다.

## 템플릿 종류

- `dev-docker-service.template.md`: 개발 서버에서 Docker Compose로 띄우는 서비스 문서
- `prod-server-encloud24.template.md`: 엔클라우드24 등 운영 서버 문서

## 프론트매터 필드 설명

### 공통
- `name`: 문서 대상의 이름
- `type`: `service` 또는 `server` (검색 필터링에 사용되는 고정값)
- `environment`: `dev` 또는 `prod`
- `doc_owner`: 문서 작성/관리 담당자
- `last_updated`: 마지막 수정일 (YYYY-MM-DD)

### 서비스 문서 전용
- `host`: 이 서비스가 도는 서버 문서 파일명 (예: `dev-docker-host.md`)
- `docker_compose_path`: 레포 내 compose 파일 경로
- `purpose`: 한 줄 설명
- `depends_on`: 의존하는 DB/서비스 목록
- `related_services`: 관련된 다른 서비스 문서 파일명 목록

### 서버 문서 전용
- `provider`: 이 서버를 운영하는 곳 (예: 자체 서버, 엔클라우드24 등)
- `services_running`: 이 서버에서 도는 서비스 문서 파일명 목록
- `backup_policy`: 백업 정책 요약

> **SSH 접속 대상(`ssh_target`, 포트)은 여기 안 씁니다** — 그건 실시간 조회를 위한 `servers.yaml`에 등록하는 정보입니다. 이 문서는 "설명"용, `servers.yaml`은 "AI가 실제로 접속할 때 쓰는 접속 정보"용으로 역할이 나뉩니다.

## 새 문서 만들기

1. 원하는 템플릿을 `docs/servers/` 또는 `docs/services/`로 복사
2. 파일명을 의미 있게 변경 (예: `prod-web-01.md`, `order-api.md`)
3. 프론트매터와 본문을 채움 (시크릿 제외)
4. `python -m app.cli ingest` 실행하여 색인 반영
