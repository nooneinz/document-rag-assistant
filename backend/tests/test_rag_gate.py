from app import rag


def _hit(score):
    return [{"score": score, "doc_id": "d", "filename": "x.pdf", "page": 1, "text": "t"}]


def test_low_similarity_declines_without_calling_llm(monkeypatch):
    monkeypatch.setattr(rag.vector_store, "search", lambda *a, **k: _hit(0.05))

    def boom(**k):
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr(rag, "OpenAI", boom)
    r = rag.answer_question("anything")
    assert r["sufficient"] is False and r["sources"] == []


def test_empty_index_declines_in_arabic(monkeypatch):
    monkeypatch.setattr(rag.vector_store, "search", lambda *a, **k: [])
    r = rag.answer_question("ما هي عاصمة اليابان؟")
    assert r["sufficient"] is False and "لا تتوفر" in r["answer"]


def _fake_client(reply):
    class Msg:
        content = reply

    class Choice:
        message = Msg()

    class Resp:
        choices = [Choice()]

    class Client:
        def __init__(self, **k):
            create = lambda **kw: Resp()  # noqa: E731
            self.chat = type("C", (), {"completions": type("D", (), {"create": staticmethod(create)})()})()

    return Client


def test_model_no_answer_tag_declines(monkeypatch):
    monkeypatch.setattr(rag.vector_store, "search", lambda *a, **k: _hit(0.9))
    monkeypatch.setattr(rag, "OpenAI", _fake_client(rag.NO_ANSWER_TAG))
    assert rag.answer_question("q")["sufficient"] is False


def test_good_answer_returns_sources(monkeypatch):
    monkeypatch.setattr(rag.vector_store, "search", lambda *a, **k: _hit(0.9))
    monkeypatch.setattr(rag, "OpenAI", _fake_client("It is 21 days [1]."))
    r = rag.answer_question("q")
    assert r["sufficient"] and r["sources"][0]["filename"] == "x.pdf"
