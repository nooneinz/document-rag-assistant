# Live demo image: builds the React app, then serves it and the API from one FastAPI server.
# Runs on Hugging Face Spaces (Docker SDK, port 7860) or any Docker host.

FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
# Spaces run the container as user 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    SEED_DIR=/home/user/app/sample_docs
WORKDIR /home/user/app

COPY --chown=user backend/requirements.txt backend/requirements.txt
# CPU-only torch keeps the image small (no CUDA libraries).
RUN pip install --no-cache-dir --user torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir --user -r backend/requirements.txt
# Download the embedding model at build time so the first request is fast.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

COPY --chown=user backend/ backend/
COPY --chown=user sample_docs/ sample_docs/
COPY --from=frontend --chown=user /frontend/dist frontend/dist

WORKDIR /home/user/app/backend
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
