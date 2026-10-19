"""End-to-end evaluation against the sample PDFs.

Checks (1) answerable questions mention the expected fact and cite the right file,
(2) unanswerable questions are declined. Needs OPENAI_API_KEY. Run from backend/:
    python -m scripts.evaluate
"""
import sys
from pathlib import Path

from app import rag, vector_store
from app.chunking import chunk_pages
from app.config import settings
from app.pdf_loader import extract_pages

SAMPLES = Path(__file__).resolve().parents[2] / "sample_docs"

# (question, expected substring in answer, expected source file); expected None => must decline
CASES = [
    ("What is the typical efficiency of a residential solar panel?", "22", "solar_energy.pdf"),
    ("How many years do manufacturers guarantee 80 percent output?", "25", "solar_energy.pdf"),
    ("How many days of paid annual leave do full-time employees get?", "21", "company_handbook.pdf"),
    ("كم عدد أيام الإجازة السنوية المدفوعة؟", "21", "company_handbook.pdf"),
    ("How many remote days are allowed per week?", "2", "company_handbook.pdf"),
    # Not in any file:
    ("Who won the 2018 football world cup?", None, None),
    ("What is the company's stock price?", None, None),
    ("ما هي عاصمة اليابان؟", None, None),
]


def main():
    for pdf in sorted(SAMPLES.glob("*.pdf")):
        pages = extract_pages(pdf.read_bytes())
        chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        vector_store.add_document(f"eval_{pdf.stem}", pdf.name, chunks)
    ok = 0
    try:
        for q, expected, src in CASES:
            r = rag.answer_question(q)
            if expected is None:
                passed = not r["sufficient"]
            else:
                passed = r["sufficient"] and expected in r["answer"] and any(s["filename"] == src for s in r["sources"])
            ok += passed
            print(f"[{'PASS' if passed else 'FAIL'}] {q}\n        -> {r['answer'][:110]}")
    finally:
        for pdf in SAMPLES.glob("*.pdf"):
            vector_store.delete_document(f"eval_{pdf.stem}")
    print(f"\n{ok}/{len(CASES)} passed")
    sys.exit(0 if ok == len(CASES) else 1)


if __name__ == "__main__":
    main()
