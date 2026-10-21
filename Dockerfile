# MedSource RAG — single container, no PyTorch. Targets small instances such as the
# Render free web service (512 MB RAM, 0.1 CPU); works on any Docker host.

# Stage 1: build the React frontend.
FROM node:22-slim AS web
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
    HEALTHCARE_RAG_MODEL_DIR=/app/.cache/healthcare-rag \
    HEALTHCARE_RAG_FRONTEND_DIR=/app/frontend/dist \
    HEALTHCARE_RAG_PERSIST_DIR=/app/.chroma \
    HEALTHCARE_RAG_AUTO_INGEST=/app/data/public/raw \
    HEALTHCARE_RAG_EMBEDDER=onnx \
    HEALTHCARE_RAG_THREADS=1
RUN useradd -m -u 1000 user
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install ".[api]"
COPY data ./data
COPY --from=web /web/dist ./frontend/dist
# Download the official sources from their original URLs (they are not stored in git),
# prepare the ONNX model (memory-mapped external-data format) and embed the corpus.
# The raw Hugging Face download cache is removed afterwards to keep the image small.
RUN (python -m healthcare_rag fetch || echo "WARNING: some sources could not be fetched") \
 && python -m healthcare_rag ingest --data-dir data/public/raw --reset \
 && rm -rf "$HF_HOME" \
 && chown -R user:user /app
USER user
ENV HF_HUB_OFFLINE=1
# Render injects $PORT (default 10000).
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn healthcare_rag.api:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
