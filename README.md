# MedSource RAG (healthcare-rag)

**🔗 Live demo / Démo en ligne : <https://medsource-rag.onrender.com>** · free Render instance, the first request after idle can take about a minute (cold start) · [Architecture](#architecture-current--actuelle) · [Azure target design](#scaling-to-production-on-azure-target-design--not-deployed)

![MedSource RAG – dark mode](docs/v2_desktop_dark_answer.png)

> **⚠️ Pas un avis médical / Not medical advice.** Projet de démonstration (portfolio).
> Les réponses sont des extraits de documents publics, qui peuvent être datés.
> Consultez toujours un professionnel de santé. / Demo project: answers are excerpts
> of public documents that may be outdated. Always consult a health professional.

Local, zero-cost **RAG (Retrieval-Augmented Generation)** pipeline that answers health
questions **only** from official public documents and cites the exact source passage
(file, page, chunk, similarity score). No LLM by default, no API keys, no paid API: it runs on a laptop or on Render's free plan.

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

## Architecture (current / actuelle)

> **FR –** Ce qui tourne réellement aujourd'hui : un seul conteneur Docker sur Render (offre
> gratuite), sans API payante. **EN –** What is actually deployed today: one Docker container
> on Render's free plan, no paid API.

![Current architecture – MedSource RAG on Render](docs/architecture/current-architecture.png)

<sub>Sources: [`docs/architecture/current-architecture.svg`](docs/architecture/current-architecture.svg) ·
regenerate with `python docs/architecture/make_diagrams.py --png`.</sub>

```mermaid
flowchart LR
  subgraph Client
    B[Browser] -->|loads| SPA[React SPA<br/>Vite · TS · Tailwind]
  end
  subgraph Render["Render free · Docker container"]
    API[FastAPI + uvicorn<br/>serves SPA + /api]
    subgraph Q["Query pipeline (per request)"]
      E[ONNX embedder<br/>multilingual MiniLM] --> C[(Chroma<br/>cosine)] --> F{Relevance filter<br/>≥ 0.60 and ≥ best − 0.08} --> X[Extractive answer<br/>+ citations]
    end
    subgraph I["Ingestion (docker build)"]
      FE[fetch] --> CC[clean + chunk] --> EM[embed] --> IX[index]
    end
  end
  S[(HAS · ANSM · Santé.fr ·<br/>Vaccination Info Service)] -->|A · HTTPS| FE
  IX -.->|same index at runtime| C
  B -->|1 · GET /| API
  SPA <-->|2 · POST /api/ask ⇄ cited JSON| API
  API -->|3| E
  X -->|6 · citations or refusal| API
  GH[GitHub master] -.->|push → auto-deploy| Render
```

### Request flow / Parcours d'une question

1. The browser loads `GET /`; FastAPI serves the built React SPA (static files).
2. The SPA sends `POST /api/ask` with the question and gets cited JSON back.
3. The question is embedded locally (ONNX Runtime, multilingual MiniLM-L12, 384 dims, no torch).
4. Chroma returns the top-k nearest chunks (cosine similarity).
5. The relevance filter keeps passages with score ≥ `MIN_SCORE` (0.60) **and** ≥ best − `SCORE_MARGIN` (0.08); otherwise the system refuses.
6. The extractive answerer returns the exact passages with source, page and score. There is no LLM and no text generation.

The model and the index are loaded once per process. Measured: about 300 MB peak RAM (the free instance has 512 MB) and a warm answer in about 0.2 s round-trip from a client.

### Ingestion flow / Ingestion des sources

- **A. fetch:** download the 4 official URLs (HAS, ANSM, Santé.fr, Vaccination Info Service). PDFs are kept as-is; for HTML, only the main text is extracted.
- **B. clean + chunk:** PDF de-hyphenation, then 800-character chunks with 150 overlap and stable IDs (source, page, chunk index).
- **C. embed:** the same ONNX model as at query time, in batches of 16, L2-normalised.
- **D. index:** upsert into Chroma (76 chunks today).

This runs **during `docker build`**, so the index is baked into the image. Third-party documents are downloaded at build time and never committed to Git.

### Modules

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

## Scaling to production on Azure (target design – not deployed)

> **⚠️ FR –** Architecture **cible**, non déployée : elle décrit comment passer du démonstrateur à un
> service à grande échelle. **EN –** This is a **target design, not deployed**. It shows how the
> demo would scale; no Azure resources exist for this project.

![Target architecture on Azure (not deployed)](docs/architecture/azure-target-architecture.png)

<sub>Source: [`docs/architecture/azure-target-architecture.svg`](docs/architecture/azure-target-architecture.svg).</sub>

```mermaid
flowchart LR
  U[Users] -->|1| SWA[Static Web Apps<br/>React SPA · CDN]
  U -->|2 · POST /api/ask + token| APIM[API Management<br/>optional]
  ENTRA[Entra ID] -.->|JWT| ACA
  APIM -->|3| ACA[Container Apps<br/>FastAPI · autoscale 0→N]
  ACA -->|4 · embed + hybrid top-k| AIS[(Azure AI Search)]
  ACA -->|5 · grounded generation| AOAI[Azure OpenAI]
  ACA -->|6 · answer + verified citations / refusal| U
  AIS -.-|alternative| PG[(Postgres + pgvector<br/>Azure DB / Supabase)]
  subgraph Ingestion["Scheduled ingestion · Databricks Workflows or Azure Functions"]
    SCH[Scheduler] -->|A| CR[Crawler] -->|B| ADLS[(ADLS Gen2 / Blob<br/>bronze · silver)] -->|C| PCE[Parse · chunk · embed] -->|D| UP[Index upsert]
  end
  PUB[Official publishers] --> CR
  UP -->|E| AIS
  KV[Key Vault] -.->|secrets| ACA
  ACA -.->|telemetry| MON[App Insights · Monitor]
  GHA[GitHub Actions<br/>tests → eval gate → deploy] -.-> ACA
```

| Component | Role in MedSource | Why this choice |
| --- | --- | --- |
| **Azure Static Web Apps** | Hosts the React SPA, with a preview environment per PR | Global CDN for static files; the frontend is decoupled from API scaling |
| **Azure Container Apps** | Runs the FastAPI image (retrieve → filter → generate → verify citations) | The same Docker image as today; HTTP/KEDA autoscaling with scale-to-zero; no Kubernetes to operate |
| **Azure AI Search** | Vector + BM25 hybrid search, semantic ranker, metadata filters (source, date, audience) | Managed index at scale; hybrid search helps with exact drug names and doses |
| *alt.* **Postgres + pgvector** (Azure Database for PostgreSQL or Supabase) | Same role as AI Search | Cheaper start; vectors live next to relational metadata; SQL the team already knows |
| **Databricks Workflows** *or* **Azure Functions** | Scheduled crawl → parse → chunk → embed → upsert | Databricks for large or Spark-heavy re-processing; Functions (timer trigger) for a small corpus |
| **ADLS Gen2 / Blob Storage** | Raw documents (bronze) and cleaned text and chunks (silver), versioned | Reproducible re-indexing, audit trail, licence and provenance kept per document |
| **Azure OpenAI** | Embeddings, plus a chat model that answers **only** from retrieved passages | Grounded generation in Azure data residency. Each sentence must map to a cited passage, otherwise the system refuses |
| **Microsoft Entra ID** | User sign-in (External ID) and managed identities for services | No secrets in code; access per user or role |
| **Azure Key Vault** | API keys and connection strings | Read through managed identity; rotation without redeploy |
| **Application Insights / Azure Monitor** | Traces, latency, refusal rate, token usage, cost alerts | Watch answer quality and spend, not only uptime |
| **GitHub Actions** | CI/CD: tests → **automatic eval gate** → build → push to ACR → new revision | Blocks a release if hit@k, refusal accuracy or faithfulness on the golden set drop below the baseline |
| *optional* **API Management** | Rate limits, quotas, API keys, response cache, request logging | Only if the API is opened to partners or needs per-client quotas |

### Cost drivers (no prices – check the Azure pricing calculator)

These are the main factors behind the bill. No figures are given here on purpose: prices depend on the region, the tier and usage.

- **Azure OpenAI tokens:** this is usually the largest variable cost. It grows with question volume × (prompt context + answer length). Levers: fewer and shorter passages in the prompt, a smaller model, caching of frequent answers.
- **Embeddings:** re-embedding the whole corpus costs much more than incremental updates. Embed only new or changed documents (content hash).
- **Search tier:** AI Search is billed per provisioned unit (replicas × partitions), even when idle. Postgres + pgvector, or Supabase, is cheaper at small scale.
- **Container Apps:** billed on vCPU/memory-seconds and requests. Scale-to-zero makes idle time almost free but adds cold starts; a minimum of 1 replica removes cold starts but costs money while idle.
- **Ingestion compute:** Databricks cluster time (DBUs + VMs), or Functions executions. Schedule it, and use job clusters that shut down.
- **Storage and egress:** usually small for a text corpus; it grows with document versioning.
- **Monitoring ingestion:** App Insights / Log Analytics bill per GB ingested. Sample traces and set retention.
- **API Management tier:** a fixed monthly cost for most tiers, which is why it is marked optional.

### Migration steps (from this repo to Azure)

1. **Containers:** push the existing Docker image to Azure Container Registry and run it on Container Apps, unchanged except config from env vars.
2. **Frontend:** move `frontend/dist` to Static Web Apps and point it at the API (CORS or a linked backend).
3. **Storage:** move `fetch` output to ADLS/Blob (bronze), with cleaned chunks in silver, instead of baking them into the image.
4. **Vector store:** add a `VectorStore` implementation for AI Search (or pgvector) next to `ChromaVectorStore`, and index the same chunk IDs and metadata.
5. **Ingestion job:** schedule `fetch → ingest` as a Databricks Workflow or a timer-triggered Function, and only re-embed documents whose content hash changed.
6. **Embeddings:** keep the local ONNX model, or switch to Azure OpenAI embeddings and re-index everything (the vector spaces are not compatible).
7. **Generation:** implement `LLMAnswerer` with Azure OpenAI and keep the relevance filter, plus a post-check that every sentence is supported by a cited passage.
8. **Security:** Entra ID sign-in, managed identities, secrets in Key Vault, and optionally API Management in front.
9. **Observability:** App Insights with OpenTelemetry; dashboards for latency, refusal rate and tokens.
10. **CI/CD:** GitHub Actions with OIDC to Azure. Run `pytest` and `healthcare-rag eval` as a **blocking gate** (fail below the current baseline), then deploy a new revision with traffic splitting.

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
