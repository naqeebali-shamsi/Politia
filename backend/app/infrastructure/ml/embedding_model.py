"""
Singleton loader for the sentence-transformers embedding model.

The model is loaded once on first access and reused across all requests.
This avoids the ~2-second model load penalty on every API call.
"""

import threading

_model = None
_lock = threading.Lock()

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384


def get_embedding_model():
    """Return the cached SentenceTransformer model (thread-safe singleton)."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer
                _model = SentenceTransformer(MODEL_NAME)
    return _model


def encode_texts(texts: list[str], batch_size: int = 256) -> list[list[float]]:
    """Encode a list of texts into embedding vectors."""
    model = get_embedding_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
    return embeddings.tolist()


def encode_query(text: str) -> list[float]:
    """Encode a single query string into an embedding vector."""
    model = get_embedding_model()
    embedding = model.encode([text], show_progress_bar=False)
    return embedding[0].tolist()
