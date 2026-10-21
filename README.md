# healthcare-rag

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
```

The first `ingest`/`ask` downloads the free embedding model
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (~460 MB) from Hugging Face.
Afterwards you can work offline with `HF_HUB_OFFLINE=1`. Fully offline demo without any
model: add `--embedder hashing` to both `ingest` and `ask` (lexical baseline only).

Example output:

```text
[1] santefr_lavage_des_mains.txt p.1, chunk 3 (score 0.87)
Comment se laver les mains efficacement ?
Il faut se laver les mains à l’eau et au savon (de préférence liquide) ; pendant 30 secondes, ...
```

Off-topic questions are refused:
`I cannot answer from the available source passages. Je ne peux pas répondre à partir des sources disponibles.`

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
        -> embed (local multilingual sentence-transformers) -> Chroma (local, cosine)

ask -> embed question -> top-k retrieval -> relevance filter -> extractive answer + citations
                                             (score >= floor AND >= best - margin)
```

| Module | Role |
| --- | --- |
| `sources.py` | List of official sources, `fetch` downloader (PDF as-is, HTML -> main text via trafilatura) |
| `ingestion.py` | `.txt`/`.md`/`.pdf` loading, page split, overlapping chunks with stable IDs |
| `embeddings.py` | Local sentence-transformers embedder + deterministic hashing embedder for tests |
| `vector_store.py` | Persistent local Chroma collection (cosine similarity) |
| `retrieval.py` | Top-k nearest passages |
| `answer.py` | `ExtractiveAnswerer` (default, no LLM, relevance filter) and `LLMAnswerer` interface (stub for a local LLM such as Ollama) |
| `pipeline.py`, `cli.py` | `fetch`, `ingest`, `ask` commands |

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

Notes: text-based PDFs only (no OCR); use `--reset` after changing documents, chunk
settings or the embedder; `SOURCES.md`/`README.md` files are never indexed.

## Limits

- Extractive only: the answer is the cited passages, not a synthesized sentence.
- PDF text extraction can split some words (e.g. `diurét ique`).
- Sources can change or move online; `fetch` reports failures per document.
- Citations prove traceability, not medical correctness.

## License

Code: [MIT](LICENSE) © 2026 El Bachir Mourabit. The MIT license covers the code only,
not the third-party documents downloaded by `fetch` (see `data/public/SOURCES.md`).
