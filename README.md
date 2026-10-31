# Litreview

An enterprise-grade research paper retrieval pipeline that helps researchers find the literature they need for their research.

Ask a question like *"How do large language models perform at medical question answering?"* and Litreview fetches relevant papers, searches them, and generates an answer backed by supporting papers.

## What it does

1. **Fetch** — Pulls research papers (e.g. from arXiv) for a given topic.
2. **Ingest** — Extracts and stores paper text and metadata.
3. **Search** — Finds relevant papers and passages using keyword, semantic, and hybrid similarity search.
4. **Retrieve** — Returns the most relevant papers and text chunks for the query.
5. **Generate** — Sends those passages to a language model to produce an answer with supporting papers cited.
6. **Observe** — Traces, caches, and evaluates the pipeline.
7. **Agent (planned)** — Adds a decision-making layer that can re-search, rewrite the query, or reject irrelevant questions.

This is **Retrieval-Augmented Generation (RAG)** — grounding LLM answers in retrieved sources instead of relying on the model's memory. The agentic version wraps retrieval in a workflow that decides *what to do next*.

## Status

Early stage. Implemented: the Postgres-backed API, OpenSearch keyword and semantic (k-NN) search, hybrid RRF retrieval, paper-level and chunk-level RAG answer generation via OpenRouter, and chunk ingestion/indexing. Real-world arXiv ingestion is planned (see `Documentation/INGESTION_PLAN.md`); the agentic workflow is on the roadmap.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with the engine running)
- [uv](https://docs.astral.sh/uv/) (Python 3.12 is managed by uv)
- An [OpenRouter](https://openrouter.ai/) API key (required by `/ask` and `/ask/chunks`)

## Setup

```powershell
uv sync                         # install dependencies into .venv
Copy-Item .env.example .env     # then set OPENROUTER_API_KEY in .env
docker compose up -d            # start Postgres and OpenSearch
uv run python .\init_db.py          # create tables and seed sample papers (Postgres)
uv run python .\semantic_search.py  # create semantic index + embeddings (required for /search/hybrid and /ask)
uv run python .\search_engine.py    # create keyword index used by /search/advanced
uv run python .\ingest.py           # optional: sync Postgres papers into the semantic index
uv run uvicorn main:app --reload    # start the API at http://127.0.0.1:8000
```

The chunk-level pipeline additionally needs its own k-NN index. Create it once:

```powershell
$body = '{"settings":{"index":{"knn":true}},"mappings":{"properties":{"paper_id":{"type":"integer"},"chunk_id":{"type":"integer"},"title":{"type":"text"},"year":{"type":"integer"},"chunk_text":{"type":"text"},"text_vector":{"type":"knn_vector","dimension":384,"method":{"name":"hnsw","engine":"lucene","space_type":"cosinesimil"}}}}}'
Invoke-RestMethod -Method Put -Uri http://localhost:9200/research-paper-chunks `
  -ContentType 'application/json' -Body $body
uv run python .\chunk_ingest.py     # chunk abstracts and index them (required for /ask/chunks)
```

## Configuration

Configuration is read from environment variables (`.env` is loaded by `llm_client.py`):

| Variable           | Required          | Description                                                        |
| ------------------ | ----------------- | ------------------------------------------------------------------ |
| `OPENROUTER_API_KEY` | yes (for `/ask`) | OpenRouter API key                                                  |
| `OPENROUTER_MODEL`   | no               | Model ID; defaults to `nvidia/nemotron-3-ultra-550b-a55b:free`      |
| `DATABASE_URL`       | no               | Defaults to `postgresql://rag_user:local_dev_password@localhost:5433/papers_db` |

`llm_client.py` raises at import time if `OPENROUTER_API_KEY` is missing, so `.env` must be configured before starting the API or running tests.

## Services

| Service    | Host port | Notes                                                        |
| ---------- | --------- | ------------------------------------------------------------ |
| API        | `8000`    | FastAPI, interactive docs at `/docs`                         |
| Postgres   | `5433`    | Mapped to container port 5432 to avoid the native Windows PostgreSQL service |
| OpenSearch | `9200`    | Security plugin disabled for local development               |

## Project layout

| File                 | Purpose                                                        |
| -------------------- | -------------------------------------------------------------- |
| `main.py`            | FastAPI app and routes                                          |
| `db.py`              | Postgres connection, schema, seed data                          |
| `init_db.py`         | Creates and seeds the Postgres database                         |
| `semantic_search.py` | Embeddings and k-NN index (`research-papers-semantic`)          |
| `search_engine.py`   | Keyword index (`research-papers-v2`) used by `/search/advanced` |
| `ingest.py`          | Syncs Postgres papers into the semantic index                   |
| `chunk_ingest.py`    | Chunks paper abstracts and indexes them into `research-paper-chunks` |
| `chunk_search.py`    | k-NN search over indexed chunks                                  |
| `chunk_rag.py`       | Chunk-level RAG pipeline (retrieve passages → generate answer)  |
| `hybrid_search.py`   | RRF fusion of BM25 and k-NN results                              |
| `rag_pipeline.py`    | Builds paper-level RAG context/prompt and generates answers      |
| `llm_client.py`      | OpenRouter client (Nemotron)                                     |
| `chunking.py`        | Word-based text chunking with configurable size and overlap      |

## API

| Method | Route               | Description                                              |
| ------ | ------------------- | -------------------------------------------------------- |
| GET    | `/health`           | Liveness probe                                           |
| GET    | `/papers`           | List all papers from Postgres                            |
| GET    | `/search?q=`        | Case-insensitive title search in Postgres (`ILIKE`)      |
| GET    | `/search/advanced`  | OpenSearch full-text search (`q`, `year`, `page`, `page_size`) |
| GET    | `/search/hybrid`    | Hybrid BM25 + k-NN search with RRF fusion (`q`, `limit`) |
| POST   | `/ask`              | Generate a grounded answer from retrieved papers; JSON body `{"question": "..."}` |
| POST   | `/ask/chunks`       | Generate a grounded answer from retrieved text chunks; JSON body `{"question": "..."}` |

Two RAG flows are available: `/ask` retrieves whole papers (hybrid BM25 + semantic search) before answering, while `/ask/chunks` retrieves paragraph-level passages (k-NN over `research-paper-chunks`) and cites the matching chunks.

Examples:

```
http://127.0.0.1:8000/search/advanced?q=medical&year=2025
http://127.0.0.1:8000/search/hybrid?q=retrieval augmented generation&limit=3
```

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask `
  -ContentType 'application/json' `
  -Body '{"question": "What are the symptoms of a heart attack?"}'

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask/chunks `
  -ContentType 'application/json' `
  -Body '{"question": "How can AI support clinical diagnosis?"}'
```

## Testing

```powershell
docker compose up -d
uv run pytest -v
```

The tests hit the real Postgres and OpenSearch services, so both containers must be running. `.env` must contain `OPENROUTER_API_KEY` because the LLM client is imported at startup; the actual LLM calls are mocked in tests.
