from openai import OpenAI

from . import vector_store
from .config import settings

NO_ANSWER_TAG = "[[NO_ANSWER]]"

SYSTEM_PROMPT = f"""You are a document assistant. Answer ONLY from the numbered context passages provided.
- Cite the passages you used like [1], [2].
- Answer in the same language as the user's question.
- If the passages do not contain enough information to answer, reply with exactly {NO_ANSWER_TAG} and nothing else.
- Never use outside knowledge and never guess."""

INSUFFICIENT = {
    "en": "I don't have enough information in the uploaded documents to answer this question.",
    "ar": "لا تتوفر معلومات كافية في المستندات المرفوعة للإجابة عن هذا السؤال.",
}


def _is_arabic(text: str) -> bool:
    return sum("؀" <= c <= "ۿ" for c in text) > len(text) * 0.3


def _insufficient(question: str) -> dict:
    return {"answer": INSUFFICIENT["ar" if _is_arabic(question) else "en"], "sufficient": False, "sources": []}


def answer_question(question: str, doc_ids: list[str] | None = None) -> dict:
    hits = vector_store.search(question, settings.top_k, doc_ids)
    # Retrieval gate: no relevant chunk at all -> skip the LLM entirely.
    if not hits or hits[0]["score"] < settings.min_similarity:
        return _insufficient(question)

    context = "\n\n".join(
        f"[{i}] ({h['filename']}, page {h['page']})\n{h['text']}" for i, h in enumerate(hits, start=1)
    )
    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    answer = (resp.choices[0].message.content or "").strip()
    # Generation gate: the model itself judged the context insufficient.
    if NO_ANSWER_TAG in answer:
        return _insufficient(question)

    sources = [
        {"id": i, "doc_id": h["doc_id"], "filename": h["filename"], "page": h["page"], "score": h["score"], "text": h["text"]}
        for i, h in enumerate(hits, start=1)
    ]
    return {"answer": answer, "sufficient": True, "sources": sources}
