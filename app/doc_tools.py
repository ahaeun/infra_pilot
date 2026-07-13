import re
from datetime import date

import yaml

from app.config import DOCS_DIR
from app.ingest import run_ingest


def _slugify(name):
    return re.sub(r"\s+", "-", name.strip())


def register_doc(name: str, doc_type: str, environment: str, purpose: str, body_markdown: str) -> str:
    """서버 또는 서비스에 대한 설명 문서를 docs/에 새로 작성하고 바로 색인합니다.
    사용자가 채팅으로 서버/서비스에 대한 설명(용도, 배포 방법, 트러블슈팅 등 정적인 정보)을 알려주면 이 도구로 문서를 만드세요.
    이미 같은 이름의 문서가 있으면 실행하지 말고 사용자에게 직접 파일을 수정하라고 안내하세요 (기존 내용을 덮어쓰지 않기 위함).
    비밀번호, API 키 등 시크릿 값은 절대 body_markdown에 포함하지 마세요 — "credentials_location: 1Password 등 어디 보관되어 있는지"처럼 위치만 표현하세요.
    사용자가 실제로 말하지 않은 내용은 지어내지 말고, 들은 내용만 정리해서 작성하세요.

    Args:
        name: 문서 대상 이름 (예: "운영2", "order-api")
        doc_type: "server" 또는 "service"
        environment: "dev" 또는 "prod"
        purpose: 한 줄 용도 설명
        body_markdown: 본문 내용. "## 개요", "## 배포 방법"처럼 마크다운 헤딩으로 구조화해서 작성.
    """
    if doc_type not in ("server", "service"):
        return "오류: doc_type은 'server' 또는 'service'여야 합니다."

    folder = "servers" if doc_type == "server" else "services"
    path = DOCS_DIR / folder / f"{_slugify(name)}.md"

    if path.exists():
        return f"오류: '{name}' 문서가 이미 존재합니다 ({path}). 기존 내용을 보존하기 위해 자동으로 덮어쓰지 않습니다. 직접 파일을 열어 수정해주세요."

    frontmatter = {
        "name": name,
        "type": doc_type,
        "environment": environment,
        "purpose": purpose,
        "doc_owner": "",
        "last_updated": date.today().isoformat(),
    }
    content = "---\n" + yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + body_markdown

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run_ingest()

    return f"'{name}' 문서를 {path.relative_to(DOCS_DIR.parent)}에 새로 작성하고 색인까지 반영했습니다."
