import chromadb

from .chunking import Chunk
from .config import settings
from .embeddings import embed

_client = None


def _collection():
    global _client
    if _client is None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(settings.data_dir / "chroma"))
    return _client.get_or_create_collection("documents", metadata={"hnsw:space": "cosine"})


def add_document(doc_id: str, filename: str, chunks: list[Chunk]) -> None:
    col = _collection()
    col.add(
        ids=[f"{doc_id}:{c.index}" for c in chunks],
        documents=[c.text for c in chunks],
        embeddings=embed([c.text for c in chunks]),
        metadatas=[{"doc_id": doc_id, "filename": filename, "page": c.page, "chunk": c.index} for c in chunks],
    )


def search(question: str, k: int, doc_ids: list[str] | None = None) -> list[dict]:
    col = _collection()
    if col.count() == 0:
        return []
    where = None
    if doc_ids:
        where = {"doc_id": doc_ids[0]} if len(doc_ids) == 1 else {"doc_id": {"$in": doc_ids}}
    res = col.query(query_embeddings=embed([question]), n_results=k, where=where)
    hits = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({**meta, "text": text, "score": round(1 - dist, 4)})  # cosine distance -> similarity
    return hits


def list_documents() -> list[dict]:
    got = _collection().get(include=["metadatas"])
    docs: dict[str, dict] = {}
    for m in got["metadatas"]:
        d = docs.setdefault(m["doc_id"], {"doc_id": m["doc_id"], "filename": m["filename"], "chunks": 0})
        d["chunks"] += 1
    return sorted(docs.values(), key=lambda d: d["filename"])


def delete_document(doc_id: str) -> None:
    _collection().delete(where={"doc_id": doc_id})
