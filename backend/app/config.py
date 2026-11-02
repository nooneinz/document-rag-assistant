from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 4
    min_similarity: float = 0.30
    data_dir: Path = BASE_DIR / "data"
    max_upload_mb: int = 10
    # Built React app (npm run build); served by FastAPI when it exists.
    frontend_dir: Path = BASE_DIR.parent / "frontend" / "dist"
    # If set, PDFs in this folder are indexed on startup when the store is empty (live demo).
    seed_dir: Path | None = None


settings = Settings()
