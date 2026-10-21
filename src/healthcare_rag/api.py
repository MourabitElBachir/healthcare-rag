"""FastAPI backend: JSON API + static single-page frontend.

Run locally:  uvicorn healthcare_rag.api:app --port 7860
Environment:
  HEALTHCARE_RAG_EMBEDDER     "st" (default) or "hashing" (offline tests)
  HEALTHCARE_RAG_FRONTEND_DIR built frontend directory (default: frontend/dist)
  HEALTHCARE_RAG_AUTO_INGEST  directory to ingest at startup if the index is empty
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Config
from .embeddings import Embedder
from .pipeline import answer_question, build_index, load_components
from .sources import SOURCES
from .vector_store import ChromaVectorStore

SOURCE_BY_FILE = {s.filename: s for s in SOURCES}
REFUSAL = {"fr": "Je ne peux pas répondre à partir des sources disponibles.",
           "en": "I cannot answer from the available source passages."}


def _embedder_name() -> str:
    return os.getenv("HEALTHCARE_RAG_EMBEDDER", "st")


@lru_cache(maxsize=1)
def get_components() -> tuple[Embedder, ChromaVectorStore]:
    """Load the embedding model and the Chroma store once per process."""
    encoder, store = load_components(_embedder_name())
    encoder.embed(["warm-up"])
    return encoder, store


@asynccontextmanager
async def lifespan(_: FastAPI):
    auto_dir = os.getenv("HEALTHCARE_RAG_AUTO_INGEST")
    if auto_dir and Path(auto_dir).is_dir():
        _, store = get_components()
        if store.collection.count() == 0:
            build_index(auto_dir, embedder=_embedder_name())
    yield


app = FastAPI(title="MedSource RAG API", version="0.2.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    k: int | None = Field(default=None, ge=1, le=10)


class Citation(BaseModel):
    rank: int
    source: str
    title: str | None
    publisher: str | None
    url: str | None
    page: int
    chunk_index: int
    score: float
    text: str


class AskResponse(BaseModel):
    question: str
    refused: bool
    message: dict[str, str] | None
    citations: list[Citation]
    k: int
    min_score: float
    score_margin: float
    took_ms: int


@app.get("/api/health")
def health() -> dict:
    config = Config.from_env()
    _, store = get_components()
    return {"status": "ok", "chunks": store.collection.count(),
            "embedder": _embedder_name(), "model": config.model_name}


@app.get("/api/sources")
def sources() -> list[dict]:
    return [{"filename": s.filename, "title": s.title, "publisher": s.publisher,
             "url": s.url, "kind": s.kind} for s in SOURCES]


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if not request.question.strip():
        raise HTTPException(422, "Empty question")
    config = Config.from_env()
    k = request.k or config.top_k
    start = time.perf_counter()
    encoder, store = get_components()
    answer = answer_question(request.question, encoder, store, k=k, config=config)
    citations = []
    for rank, p in enumerate(answer.citations, 1):
        meta = SOURCE_BY_FILE.get(Path(p.source).name)
        citations.append(Citation(
            rank=rank, source=p.source, page=p.page, chunk_index=p.chunk_index,
            score=round(p.score, 4), text=p.text,
            title=meta.title if meta else None, publisher=meta.publisher if meta else None,
            url=meta.url if meta else None))
    return AskResponse(
        question=request.question, refused=not citations,
        message=None if citations else REFUSAL, citations=citations, k=k,
        min_score=config.min_score, score_margin=config.score_margin,
        took_ms=round((time.perf_counter() - start) * 1000))


def _mount_frontend() -> None:
    dist = Path(os.getenv("HEALTHCARE_RAG_FRONTEND_DIR",
                          Path(__file__).resolve().parents[2] / "frontend" / "dist"))
    if not (dist / "index.html").is_file():
        return
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and dist.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")


_mount_frontend()
