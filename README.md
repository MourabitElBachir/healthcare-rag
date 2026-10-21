# MedSource RAG (healthcare-rag)

![MedSource RAG – dark mode](docs/v2_desktop_dark_answer.png)

> **⚠️ Pas un avis médical / Not medical advice.** Projet de démonstration (portfolio).
> Les réponses sont des extraits de documents publics, qui peuvent être datés.
> Consultez toujours un professionnel de santé. / Demo project: answers are excerpts
> of public documents that may be outdated. Always consult a health professional.

Local, zero-cost **RAG (Retrieval-Augmented Generation)** pipeline that answers health
questions **only** from official public documents and cites the exact source passage
(file, page, chunk, similarity score). No LLM by default, no API keys, no cloud.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"            # or: pip install -r requirements.txt && pip install -e .

python -m healthcare_rag fetch     # download official sources into data/public/raw/ (git-ignored)
python -m healthcare_rag ingest --data-dir data/public/raw --reset
python -m healthcare_rag ask "Combien de temps faut-il se laver les mains ?" -k 4

pytest                             # offline tests, no model download

pip install -e ".[ui]"             # optional: Streamlit demo
streamlit run src/healthcare_rag/app.py
python -m healthcare_rag eval -k 4 # small retrieval evaluation (see below)
```

The first `ingest`/`ask` downloads the free multilingual embedding model
`paraphrase-multilingual-MiniLM-L12-v2` as an ONNX export (~470 MB, once) and runs it with
**onnxruntime — no PyTorch**. Afterwards you can work offline with `HF_HUB_OFFLINE=1`.
Fully offline demo without any model: add `--embedder hashing` to both `ingest` and `ask`
(lexical baseline only).

### Embedding backends

| `--embedder` / `HEALTHCARE_RAG_EMBEDDER` | Install | Notes |
| --- | --- | --- |
| `onnx` (default) | base install | onnxruntime + SentencePiece, fp32 ONNX weights memory-mapped (external data). Same vectors as sentence-transformers (cosine 1.000000 on our checks), API peak RAM ≈ 300 MB |
| `onnx` + `HEALTHCARE_RAG_ONNX_VARIANT=int8` | base install | int8 export, lower RAM, slightly lower quality (hit@4 8/10 instead of 9/10 with the default thresholds) |
| `st` | `pip install -e ".[st]"` | sentence-transformers + PyTorch (reference implementation, much heavier install and RAM) |
| `hashing` | base install | deterministic lexical baseline used by the tests |

Why it is lean: the Hugging Face `tokenizer.json` of this 250k-token multilingual model
costs ~285 MB of RAM, so the ONNX backend uses the original XLM-R
`sentencepiece.bpe.model` with the fairseq id mapping (identical ids on all 602 corpus
lines and questions tested, ~95 MB); and the ONNX weights are converted once to external
data so onnxruntime memory-maps them and only the embedding rows actually used are paged
in. Switching backend requires `ingest --reset`.

Example output:

```text
[1] santefr_lavage_des_mains.txt p.1, chunk 3 (score 0.87)
Comment se laver les mains efficacement ?
Il faut se laver les mains à l’eau et au savon (de préférence liquide) ; pendant 30 secondes, ...
```

Off-topic questions are refused:
`I cannot answer from the available source passages. Je ne peux pas répondre à partir des sources disponibles.`

## Web app (FastAPI + React)

A single-page app (Vite + React 19 + TypeScript + Tailwind CSS v4, self-hosted Inter /
Geist Mono fonts) served by a FastAPI backend that wraps the same pipeline. The
embedding model and the index are loaded once per process, so a question takes tens of
milliseconds after start-up.

```bash
pip install -e ".[api]"
cd frontend && npm ci && npm run build && cd ..
uvicorn healthcare_rag.api:app --port 7860        # http://localhost:7860 (no PyTorch needed)
# frontend dev server with hot reload (proxies /api to :7860): cd frontend && npm run dev
```

API:

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | status, number of indexed chunks, embedding model |
| `GET /api/sources` | the official documents (title, publisher, URL) |
| `POST /api/ask` `{"question": "...", "k": 4}` | `refused`, bilingual refusal `message`, `citations[]` (rank, source, title, publisher, url, page, chunk_index, score, text), `took_ms` |

UI features: chat layout, dark mode (default) and light mode, FR/EN labels, medical
disclaimer banner, suggested questions, citation cards (score bar, page/fragment,
expandable passage, copy, link to the official source), distinct refusal and error
states, animated search state, sources/index side panel, mobile layout, keyboard and
screen-reader support (landmarks, `aria-live`, visible focus).

| Light mode (EN labels) | Off-topic refusal | Mobile |
| --- | --- | --- |
| ![Light](docs/v2_desktop_light_answer.png) | ![Refusal](docs/v2_desktop_dark_refusal.png) | ![Mobile](docs/v2_mobile_dark_answer.png) |

Empty state: ![Home](docs/v2_desktop_dark_empty.png)

### Deploy for free on Render (Docker)

The `Dockerfile` is a multi-stage build without PyTorch: `node:22-slim` builds the
frontend, then `python:3.12-slim` installs the API, downloads the official sources from
their URLs, prepares the ONNX model and embeds the corpus **at build time**, and serves
everything with uvicorn on `$PORT` (Render injects it; default **10000**), as uid 1000.

Measured locally with the same steps (no Docker): API peak RAM ≈ **300 MB** after model
load and queries (fits the 512 MB free instance), ~15 ms per question.

1. Fork/push this repository to GitHub.
2. On [Render](https://render.com): **New → Blueprint**, select the repository; it reads
   [`render.yaml`](render.yaml) (free plan, Docker runtime, health check `/api/health`,
   `HEALTHCARE_RAG_THREADS=1`). Or create a **Web Service** with runtime *Docker*.
3. Wait for the build (sources + model download), then open the service URL.

Free instances sleep after ~15 minutes without traffic; the next request wakes the
service (cold start of tens of seconds). Any other Docker host works too:

```bash
docker build -t medsource-rag .
docker run -p 10000:10000 medsource-rag     # http://localhost:10000
```

## Streamlit demo (fallback)

```bash
pip install -e ".[ui]"
streamlit run src/healthcare_rag/app.py      # http://localhost:8501  (?q=... pre-fills the question)
```

Question box, top-k slider, cited passages with source / page / chunk / score, refusal
message, sidebar disclaimer and source list. The embedding model and the Chroma index are
cached with `st.cache_resource`, so only the first question pays the model-loading cost.

| Cited answer | Off-topic refusal |
| --- | --- |
| ![Cited answer](docs/screenshot_answer.png) | ![Refusal](docs/screenshot_refusal.png) |

## Evaluation

`eval/questions.jsonl` holds 12 French questions written from the 4 official documents:
10 answerable (each with the expected source file) and 2 off-topic (expected refusal).

```bash
python -m healthcare_rag eval -k 4
```

- **hit@k** = share of answerable questions whose expected source is among the cited
  passages (after the relevance filter).
- **refusal accuracy** = share of off-topic questions that were refused.

Result on 2026-10-21 (default model, `k=4`, `MIN_SCORE=0.6`, `SCORE_MARGIN=0.08`):

| Metric | Value |
| --- | --- |
| hit@4 | **9/10 = 0.90** |
| false refusals | 1 (« Comment réaliser une automesure tensionnelle à domicile ? ») |
| refusal accuracy | **2/2 = 1.00** |

The miss is a retrieval failure: the HAS section on home blood-pressure self-measurement
was not in the top 4 (best score 0.47 < 0.6), so the system refused rather than citing a
weak passage. This set is tiny and was written by the author; treat it as a smoke test,
not a benchmark.

## FR – Le problème

Les soignants et les patients perdent du temps à chercher une information fiable dans
des documents de santé longs (recommandations HAS, pages ANSM, etc.). Un chatbot
généraliste peut inventer des réponses, ce qui est dangereux en santé. Ce projet répond
uniquement à partir d'un corpus de sources officielles et cite le passage exact, pour que
chaque réponse soit vérifiable.

## EN – The problem

Finding reliable information in long official health documents is slow, and general
chatbots can hallucinate. This project only answers from a curated corpus of official
sources and always cites the exact passage, so every answer can be checked.

## Architecture

```text
fetch (official URLs) -> data/public/raw/ (PDF + HTML-to-text)
        |
ingest -> load pages -> chunk (800 chars, 150 overlap, source/page metadata)
        -> embed (multilingual MiniLM, local ONNX Runtime) -> Chroma (local, cosine)

ask -> embed question -> top-k retrieval -> relevance filter -> extractive answer + citations
                                             (score >= floor AND >= best - margin)
```

| Module | Role |
| --- | --- |
| `sources.py` | List of official sources, `fetch` downloader (PDF as-is, HTML -> main text via trafilatura) |
| `ingestion.py` | `.txt`/`.md`/`.pdf` loading, page split, overlapping chunks with stable IDs |
| `embeddings.py` | ONNX Runtime embedder (default), optional sentence-transformers embedder, hashing embedder for tests |
| `vector_store.py` | Persistent local Chroma collection (cosine similarity) |
| `retrieval.py` | Top-k nearest passages |
| `answer.py` | `ExtractiveAnswerer` (default, no LLM, relevance filter) and `LLMAnswerer` interface (stub for a local LLM such as Ollama) |
| `pipeline.py`, `cli.py` | `fetch`, `ingest`, `ask`, `eval` commands |
| `evaluation.py` | hit@k / refusal-accuracy evaluation on a JSONL question set |
| `api.py` | FastAPI backend (`/api/ask`, `/api/health`, `/api/sources`) + static frontend |
| `app.py` | Streamlit demo UI (fallback) |
| `frontend/` | React + TypeScript + Tailwind single-page app |

### Relevance filter

A retrieved passage is cited only if its cosine score is **≥ `MIN_SCORE`** (absolute
floor, default 0.6) **and ≥ best score − `SCORE_MARGIN`** (default 0.08). If nothing
passes, the system refuses to answer. Thresholds are heuristics tuned on the demo
corpus; they do not guarantee relevance.

## Data / Données

- `data/public/SOURCES.md` lists the official documents used (title, publisher, URL,
  retrieval date, reuse note as stated by each site): HAS & SFHTA (hypertension memo,
  PDF), ANSM (paracetamol), Santé.fr (hand washing), Vaccination Info Service / Santé
  publique France (flu vaccination).
- **These third-party documents are not included in this repository.** Run
  `python -m healthcare_rag fetch` to download them from their original URLs into
  `data/public/raw/` (git-ignored). Their content belongs to their publishers.
- `data/sample/` contains short **fictional** sample texts written for tests and demos
  (clearly labeled, not official, not medical advice).

## Configuration

Environment variables prefixed with `HEALTHCARE_RAG_`:

| Variable | Default |
| --- | --- |
| `MODEL_NAME` | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| `PERSIST_DIR` | .chroma |
| `COLLECTION_NAME` | healthcare_rag |
| `CHUNK_SIZE` / `OVERLAP` | 800 / 150 characters |
| `TOP_K` | 4 |
| `MIN_SCORE` | 0.6 (cosine similarity floor) |
| `SCORE_MARGIN` | 0.08 (max gap to the best passage) |
| `EMBEDDER` | onnx (`st`, `hashing`) |
| `ONNX_VARIANT` | fp32 (`int8`) |
| `MODEL_DIR` | ~/.cache/healthcare-rag (prepared ONNX model) |
| `THREADS` | onnxruntime default (set 1 on tiny instances) |

Notes: text-based PDFs only (no OCR); use `--reset` after changing documents, chunk
settings or the embedder; `SOURCES.md`/`README.md` files are never indexed.

## Limits

- Extractive only: the answer is the cited passages, not a synthesized sentence.
- PDF text is lightly cleaned (end-of-line hyphenation such as `néces-`/`site` is re-joined), but
  some mid-line splits remain (e.g. `diurét ique`).
- Sources can change or move online; `fetch` reports failures per document.
- Citations prove traceability, not medical correctness.

## License

Code: [MIT](LICENSE) © 2026 El Bachir Mourabit. The MIT license covers the code only,
not the third-party documents downloaded by `fetch` (see `data/public/SOURCES.md`).
