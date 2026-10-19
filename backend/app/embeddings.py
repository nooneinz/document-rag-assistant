from functools import lru_cache

from .config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()
