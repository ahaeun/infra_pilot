# infra_pilot

인프라(개발 서버 Docker, 운영 서버 등)를 이해하고 질문에 답해주는 Q&A 어시스턴트입니다. 두 가지 방식으로 답변합니다.

1. **문서 기반(RAG)** — `docs/`에 색인된 설명 문서를 검색해서 정적인 정보(용도, 배포 방법, 설정 위치 등)에 답변
2. **실시간 조회** — "운영2 용량 알려줘" 같은 질문은 `servers.yaml`에 등록된 서버에 SSH로 직접 접속해서 지금 이 순간의 값(디스크 용량, 메모리, 컨테이너 목록, 가동 시간)을 확인 후 답변

## 폴더 구조

```
infra_pilot/
├── docs/                  # 실제 색인 대상 문서 (계속 채워나가는 곳)
│   ├── servers/
│   └── services/
├── docs_templates/        # 새 문서 작성용 템플릿 (색인 안 됨)
├── servers.yaml           # SSH 접속 대상 목록 (git에 커밋되지 않음, 직접 생성)
└── app/                   # 파이썬 패키지
    ├── config.py
    ├── chunking.py
    ├── embeddings.py
    ├── vectorstore.py
    ├── ingest.py
    ├── ssh_tools.py       # 실시간 서버 진단 도구 (디스크/메모리/컨테이너/가동시간)
    ├── qa.py
    ├── cli.py
    ├── main.py            # 로컬 웹 채팅 화면 (FastAPI)
    └── templates/
        └── index.html
```

## 설치

```bash
cp .env.example .env
# .env 파일을 열어 GEMINI_API_KEY, VOYAGE_API_KEY 입력

pip install -r requirements.txt
```

## 사용법

### 1. 문서 작성 (정적 정보용)

`docs_templates/`의 템플릿을 참고해서 `docs/servers/` 또는 `docs/services/`에 문서를 작성하세요. 시크릿(비밀번호, API 키 등)은 절대 문서에 적지 마세요 — `docs_templates/README.md`를 꼭 읽어보세요.

### 2. 서버 접속 정보 등록 (실시간 조회용)

```bash
cp servers.yaml.example servers.yaml
```

`servers.yaml`을 열어서 질문할 때 부를 서버 이름과 SSH 접속 대상을 등록하세요. `ssh_target`은 평소 터미널에서 `ssh <값>`이라고 입력할 때 쓰는 값(또는 `~/.ssh/config`의 Host 별칭)과 동일해야 합니다. **비밀번호나 SSH 키는 절대 이 파일에 넣지 마세요** — 실제 인증은 이미 설정된 `~/.ssh/config`/SSH 에이전트/키가 담당합니다.

### 3. 색인

```bash
python -m app.cli ingest
```

### 4. 질문

```bash
python -m app.cli ask "개발 서버에서 도는 서비스는 뭐야?"
python -m app.cli ask "운영2 용량 알려줘"
```

### 5. 웹 채팅 화면으로 쓰기

터미널 명령어 대신 브라우저에서 채팅하듯 쓸 수도 있습니다.

```bash
python -m app.cli serve
```

실행 후 브라우저에서 http://localhost:8090 을 열면 됩니다. CLI의 `ask`와 동일한 로직을 사용하며, 문서 기반 질문과 실시간 서버 조회 모두 그대로 동작합니다.

## 참고

- 문서 기반 답변은 `docs/`에 색인된 내용에만 근거합니다. 문서에 없는 내용은 "문서에서 찾을 수 없습니다"라고 답합니다.
- 실시간 조회는 `df -h`, `free -h`, `docker ps`, `uptime`처럼 정해진 읽기 전용 명령만 실행합니다. 서버 설정을 변경하거나 파일을 쓰는 동작은 하지 않습니다.
- `servers.yaml`에 등록되지 않은 서버 이름을 물어보면 등록된 서버 목록을 안내합니다.
