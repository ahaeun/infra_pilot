from app.chunking import build_chunks, parse_document
from app.config import DOCS_DIR
from app.embeddings import embed_documents
from app.vectorstore import rebuild_collection, upsert_chunks

REQUIRED_FIELDS = ("name", "type")


def discover_doc_files():
    return sorted(DOCS_DIR.rglob("*.md"))


def run_ingest():
    doc_files = discover_doc_files()
    collection = rebuild_collection()

    all_chunks = []
    indexed_file_count = 0
    skipped = []

    for path in doc_files:
        metadata, body = parse_document(path)
        missing = [f for f in REQUIRED_FIELDS if not metadata.get(f)]
        if missing:
            skipped.append((path, missing))
            continue

        relative_path = str(path.relative_to(DOCS_DIR.parent))
        all_chunks.extend(build_chunks(relative_path, metadata, body))
        indexed_file_count += 1

    if all_chunks:
        embeddings = embed_documents([c["text"] for c in all_chunks])
        upsert_chunks(collection, all_chunks, embeddings)

    print(f"{indexed_file_count}개 파일에서 {len(all_chunks)}개 청크를 색인했습니다.")
    for path, missing in skipped:
        print(f"경고: {path} - 필수 필드 누락({', '.join(missing)})으로 건너뜀")


if __name__ == "__main__":
    run_ingest()
