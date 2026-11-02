import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import rag, vector_store
from .chunking import chunk_pages
from .config import settings
from .pdf_loader import extract_pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Live demo: start with the sample PDFs so visitors can ask right away.
    if settings.seed_dir and not vector_store.list_documents():
        for path in sorted(settings.seed_dir.glob("*.pdf")):
            index_pdf(path.name, path.read_bytes())
    yield


app = FastAPI(title="Document RAG Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    doc_ids: list[str] | None = None


@app.post("/api/documents")
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"PDF is larger than {settings.max_upload_mb} MB.")
    return index_pdf(file.filename, data)


def index_pdf(filename: str, data: bytes) -> dict:
    try:
        pages = extract_pages(data)
    except Exception:
        raise HTTPException(400, "Could not read this PDF.")
    if not pages:
        raise HTTPException(422, "No extractable text found (scanned PDF?).")
    chunks = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
    doc_id = uuid.uuid4().hex[:12]
    vector_store.add_document(doc_id, filename, chunks)
    # Keep the original so the UI can show it next to the chat.
    pdf_dir = settings.data_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    (pdf_dir / f"{doc_id}.pdf").write_bytes(data)
    return {"doc_id": doc_id, "filename": filename, "pages": len(pages), "chunks": len(chunks)}


@app.get("/api/documents")
def documents():
    return vector_store.list_documents()


@app.get("/api/documents/{doc_id}/file")
def document_file(doc_id: str):
    path = settings.data_dir / "pdfs" / f"{doc_id}.pdf"
    if not doc_id.isalnum() or not path.exists():
        raise HTTPException(404, "Not found")
    return Response(path.read_bytes(), media_type="application/pdf")


@app.delete("/api/documents/{doc_id}")
def delete(doc_id: str):
    if not doc_id.isalnum():
        raise HTTPException(400, "Bad id")
    vector_store.delete_document(doc_id)
    (settings.data_dir / "pdfs" / f"{doc_id}.pdf").unlink(missing_ok=True)
    return {"ok": True}


@app.post("/api/ask")
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(400, "Empty question.")
    if not settings.openai_api_key:
        raise HTTPException(500, "OPENAI_API_KEY is not set (see backend/.env.example).")
    return rag.answer_question(req.question.strip(), req.doc_ids)


# Production: one server for both the API and the React app (mounted last so /api wins).
if settings.frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
