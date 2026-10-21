# MedSource RAG — single container for Hugging Face Spaces (Docker SDK, port 7860).
# Stage 1: build the React frontend.
FROM node:20-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python API + static frontend + prebuilt index.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    HEALTHCARE_RAG_FRONTEND_DIR=/app/frontend/dist \
    HEALTHCARE_RAG_PERSIST_DIR=/app/.chroma \
    HEALTHCARE_RAG_AUTO_INGEST=/app/data/public/raw
# Hugging Face Spaces runs containers as uid 1000.
RUN useradd -m -u 1000 user
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install ".[api]"
COPY data ./data
COPY --from=web /web/dist ./frontend/dist
# Download the official sources from their original URLs (they are not stored in git),
# then embed them; this also caches the free embedding model inside the image.
RUN (python -m healthcare_rag fetch || echo "WARNING: some sources could not be fetched") \
 && python -m healthcare_rag ingest --data-dir data/public/raw --reset \
 && chown -R user:user /app
USER user
ENV HF_HUB_OFFLINE=1
EXPOSE 7860
CMD ["uvicorn", "healthcare_rag.api:app", "--host", "0.0.0.0", "--port", "7860"]
