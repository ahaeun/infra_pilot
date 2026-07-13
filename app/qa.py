from google import genai
from google.genai import errors, types

from app.config import GEMINI_API_KEY, GEMINI_MODEL, TOP_K
from app.doc_tools import register_doc
from app.embeddings import embed_query
from app.ssh_tools import register_server, run_readonly_diagnostic
from app.vectorstore import get_collection, query

TOOLS = [run_readonly_diagnostic, register_server, register_doc]

SYSTEM_PROMPT = """당신은 사용자의 인프라를 이해하고 답변하는 어시스턴트입니다.

네 종류의 정보 소스가 있습니다:
1. 아래 [출처] 컨텍스트 — 서버/서비스에 대한 정적인 설명 문서 (용도, 배포 방법, 설정 위치 등)
2. run_readonly_diagnostic 도구 — 서버에 SSH로 접속해서 읽기 전용 쉘 명령을 실행하고 지금 이 순간의 실제 상태를 확인
3. register_server 도구 — 사용자가 새 서버의 이름과 SSH 접속 정보를 알려주면 servers.yaml에 등록
4. register_doc 도구 — 사용자가 서버/서비스에 대한 설명(용도, 배포 방법, 트러블슈팅 등)을 채팅으로 알려주면 docs/에 새 문서로 작성

규칙:
- 실시간 상태(용량, 메모리, 프로세스, 컨테이너, 가동 시간 등)를 묻는 질문은 반드시 run_readonly_diagnostic으로 상황에 맞는 명령을 직접 만들어 실행해서 실제 값을 확인한 뒤 답하세요. 절대 문서 내용이나 기억으로 수치/상태를 지어내지 마세요.
- run_readonly_diagnostic에는 반드시 "조회"만 하는 명령을 넘기세요. 파일을 만들거나 지우거나, 프로세스/서비스/컨테이너를 재시작·중지·삭제하거나, 설정을 바꾸는 등 서버 상태를 변경하는 명령은 절대 실행하지 마세요. 사용자가 "재시작해줘", "지워줘"처럼 상태 변경을 요청해도 실행하지 말고, 이 도구로는 조회만 할 수 있다고 안내하세요.
- 사용자가 "서버 등록해줘/추가해줘"처럼 새 서버 접속 정보(이름 + user@host 형태의 접속 주소, 선택적으로 포트)를 알려주면 register_server 도구를 호출하세요. 접속 정보(ssh_target)가 명확하지 않으면 추측해서 등록하지 말고 사용자에게 정확한 값을 물어보세요. 비밀번호나 SSH 키 값은 절대 받지도, 저장하지도 마세요.
- 사용자가 서버/서비스에 대한 설명(용도, 배포 방법, 트러블슈팅 등 정적인 정보)을 채팅으로 알려주며 문서화해달라고 하면 register_doc 도구를 호출하세요. body_markdown은 사용자가 실제로 말한 내용만으로 작성하고, 말하지 않은 내용은 절대 지어내지 마세요. 비밀번호나 API 키 등 시크릿 값은 절대 문서에 포함하지 마세요.
- 그 외의 질문(설명, 설정, 배포 방법 등)은 반드시 [출처] 컨텍스트 안의 정보만 사용해서 답변하세요. 컨텍스트에 없는 내용은 절대 추측하거나 지어내지 마세요.
- [출처] 컨텍스트에 질문에 대한 답이 없고 관련 도구도 없으면 "문서에서 찾을 수 없습니다"라고 솔직히 답하세요.
- 문서 내용을 근거로 답했다면 출처 파일 경로를 언급하세요.
- 비밀번호, API 키 등 시크릿 값은 절대 생성하거나 추측하지 마세요.
- 항상 한국어로 답변하세요."""

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def build_context_block(results):
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    blocks = []
    sources = []
    for doc, meta in zip(documents, metadatas):
        source_path = meta.get("source_path", "알 수 없음")
        heading = meta.get("heading", "")
        blocks.append(f'[출처: {source_path} - "{heading}"]\n{doc}')
        sources.append(source_path)

    return "\n\n".join(blocks), list(dict.fromkeys(sources))


def answer_question(question):
    """질문에 답하고 {"answer": str, "sources": list[str]}를 반환합니다. 출력은 하지 않습니다."""
    collection = get_collection()
    query_embedding = embed_query(question)
    results = query(collection, query_embedding, TOP_K)

    if results["documents"][0]:
        context_block, sources = build_context_block(results)
    else:
        context_block, sources = "(색인된 문서가 없습니다. 실시간 서버 조회 도구만 사용 가능합니다.)", []

    user_message = f"{context_block}\n\n질문: {question}"

    try:
        response = _get_client().models.generate_content(
            model=GEMINI_MODEL,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=1024,
                tools=TOOLS,
            ),
        )
    except errors.APIError as e:
        if e.code == 404:
            error_text = f"오류: 모델 '{GEMINI_MODEL}'을 찾을 수 없습니다. .env의 GEMINI_MODEL 값을 확인하세요."
        elif e.code == 429:
            error_text = f"오류: API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.\n상세: {e.message}"
        else:
            error_text = f"오류: API 요청이 실패했습니다 ({e.code}): {e.message}"
        return {"answer": error_text, "sources": []}

    answer_text = response.text
    if not answer_text:
        finish_reason = None
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason
        answer_text = f"(답변 생성에 실패했습니다. 다시 질문해주세요. finish_reason={finish_reason})"

    return {"answer": answer_text, "sources": sources}


def ask(question):
    result = answer_question(question)
    print(result["answer"])
    if result["sources"]:
        print("\n출처:")
        for source in result["sources"]:
            print(f"- {source}")
