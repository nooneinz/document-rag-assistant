from app.chunking import chunk_pages, split_text


def test_short_text_single_chunk():
    assert split_text("hello world", 100, 10) == ["hello world"]


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = split_text(text, 200, 40)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)
    # overlap: end of one chunk reappears at the start of the next
    assert chunks[0].split()[-1] in chunks[1]


def test_chunk_pages_keeps_page_numbers():
    out = chunk_pages([(1, "a " * 300), (3, "b " * 300)], 200, 20)
    assert {c.page for c in out} == {1, 3}
    assert [c.index for c in out] == list(range(len(out)))
