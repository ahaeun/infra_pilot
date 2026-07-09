import argparse

from app.ingest import run_ingest
from app.qa import ask


def main():
    parser = argparse.ArgumentParser(prog="infra-pilot", description="인프라 문서 기반 Q&A 어시스턴트")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ingest", help="docs/ 폴더의 문서를 색인합니다")

    ask_parser = subparsers.add_parser("ask", help="인프라에 대해 질문합니다")
    ask_parser.add_argument("question", help="질문 내용")

    subparsers.add_parser("serve", help="로컬 웹 채팅 화면을 실행합니다")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest()
    elif args.command == "ask":
        ask(args.question)
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("app.main:app", host="127.0.0.1", port=8090, reload=True)


if __name__ == "__main__":
    main()
