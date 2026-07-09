import voyageai

from app.config import VOYAGE_API_KEY, VOYAGE_EMBED_MODEL

_client = voyageai.Client(api_key=VOYAGE_API_KEY)

_BATCH_SIZE = 128


def embed_documents(texts):
    embeddings = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i:i + _BATCH_SIZE]
        result = _client.embed(batch, model=VOYAGE_EMBED_MODEL, input_type="document")
        embeddings.extend(result.embeddings)
    return embeddings


def embed_query(text):
    result = _client.embed([text], model=VOYAGE_EMBED_MODEL, input_type="query")
    return result.embeddings[0]
