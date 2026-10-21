# healthcare-rag

## FR

Squelette Python local pour retrouver des passages de documents de santé et les
citer exactement : fichier, page (à partir de 1), fragment (à partir de 0).
La réponse est un extrait, sans LLM ni conseil personnalisé.

```text
documents -> ingestion -> fragments -> embeddings -> Chroma local
                                                       |
question -> embedding -> recherche <--------------------+
                            |
                     extraits + citations
```

Préparation, dans un environnement où les dépendances peuvent être installées :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m healthcare_rag ingest --data-dir data/sample --reset --embedder hashing
python -m healthcare_rag ask "hygiène des mains" -k 4 --embedder hashing
pytest
```

Aucune clé, API payante, infrastructure cloud ou Docker. `hashing` fonctionne
sans téléchargement. Le mode par défaut `st` utilise un modèle gratuit qui doit
être téléchargé une fois, puis être disponible dans le cache pour travailler
hors ligne. Pour interdire le réseau avec un modèle déjà en cache, définir
`HF_HUB_OFFLINE=1`. Utiliser le même embedder pour indexer et interroger.

**Pas un avis médical.** Les trois fichiers fournis sont des données fictives
illustratives, pas des publications officielles. Pour un corpus réel, remplacer
ces fichiers par des documents publics officiels vérifiés, puis réindexer avec
`--reset`. La sélection et la vérification des sources sont manuelles : le code
ne certifie ni leur provenance, ni leur actualité. Il cite uniquement les
passages du corpus local et refuse lorsque leur score est insuffisant.

## EN

A minimal local Python project for locating health document passages and quoting
them with exact file, page, and chunk references. Extractive answers use no LLM.

```text
ingest -> chunk -> embed -> vector store -> retrieve -> answer with citations
                                              ^
                                        embed question
```

Use the commands above; for example:

```bash
python -m healthcare_rag ask "hand hygiene" --embedder hashing
```

Use `--embedder st` (the default) for multilingual semantic retrieval after the
free model has been cached. Hashing is a deterministic lexical baseline for
fully offline demos and tests; it does not translate or understand questions.
Tests use hashing and temporary Chroma directories and never load a model.

**Not medical advice. Sample data only.** The supplied files are illustrative,
not official sources. For real exploration, curate verified official public
documents and rebuild with `ingest --data-dir YOUR_DIR --reset`. Provenance must
be checked manually. Citations establish traceability, not medical correctness.
Similarity thresholds are heuristic and cannot guarantee relevance or detect
all unsupported questions. No external search or generated medical claims.

Configuration uses `HEALTHCARE_RAG_` environment variables:

| Suffix | Default |
| --- | --- |
| MODEL_NAME | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| PERSIST_DIR | .chroma |
| COLLECTION_NAME | healthcare_rag |
| CHUNK_SIZE | 800 characters |
| OVERLAP | 150 characters |
| TOP_K | 4 |
| MIN_SCORE | 0.25 (cosine similarity) |

Supported inputs: UTF-8 `.txt`, `.md` (form-feed separates pages), and text-based
PDFs via pypdf. Scanned PDFs require OCR outside this skeleton. Chunk indices
restart on each page. Passages preserve the extracted text exactly; PDF text
order depends on extraction. Sources use paths relative to the input directory.
Re-ingestion upserts stable IDs; use `--reset` after editing/removing documents,
changing chunk settings, or switching embedding providers. Reset deletes only
the configured collection. `LLMAnswerer` is an unimplemented local-LLM extension.
