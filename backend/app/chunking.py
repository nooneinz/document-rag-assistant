from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    page: int
    index: int


def split_text(text: str, size: int, overlap: int) -> list[str]:
    """Split on character windows, preferring to end at a sentence/word boundary."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            window = text[start:end]
            cut = max(window.rfind(". "), window.rfind("? "), window.rfind("؟ "))
            if cut < size // 2:
                cut = window.rfind(" ")
            if cut > size // 2:
                end = start + cut + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_pages(pages: list[tuple[int, str]], size: int, overlap: int) -> list[Chunk]:
    out: list[Chunk] = []
    for page, text in pages:
        for piece in split_text(text, size, overlap):
            out.append(Chunk(text=piece, page=page, index=len(out)))
    return out
