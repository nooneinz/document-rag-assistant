from io import BytesIO

from pypdf import PdfReader


def extract_pages(data: bytes) -> list[tuple[int, str]]:
    """Return [(page_number, text)] (1-based), skipping pages with no extractable text."""
    reader = PdfReader(BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        if text:
            pages.append((i, text))
    return pages
