import chromadb

from app.config import CHROMA_DB_DIR, COLLECTION_NAME

_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))


def _sanitize_metadata(metadata):
    """Chroma metadata values must be str/int/float/bool — flatten lists, drop None."""
    sanitized = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, list):
            sanitized[key] = ", ".join(str(v) for v in value)
        elif isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = str(value)
    return sanitized


def rebuild_collection():
    try:
        _client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return _client.create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def get_collection():
    return _client.get_or_create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def upsert_chunks(collection, chunks, embeddings):
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[_sanitize_metadata(c["metadata"]) for c in chunks],
    )


def query(collection, query_embedding, top_k):
    return collection.query(query_embeddings=[query_embedding], n_results=top_k)
