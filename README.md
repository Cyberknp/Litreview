# Litreview

An enterprise-grade research paper retrieval pipeline that helps researchers find the literature they need for their research.

Ask a question like *"How do large language models perform at medical question answering?"* and Litreview fetches relevant papers, searches them, and generates an answer backed by supporting papers.

## What it does

1. **Fetch** — Pulls research papers (e.g. from arXiv) for a given topic.
2. **Ingest** — Extracts and stores paper text and metadata.
3. **Search** — Finds relevant passages using keyword + semantic similarity search.
4. **Retrieve** — Returns the most relevant passages for the query.
5. **Generate** — Sends those passages to a language model to produce an answer with supporting papers cited.
6. **Observe** — Traces, caches, and evaluates the pipeline.
7. **Agent (planned)** — Adds a decision-making layer that can re-search, rewrite the query, or reject irrelevant questions.

This is **Retrieval-Augmented Generation (RAG)** — grounding LLM answers in retrieved sources instead of relying on the model's memory. The agentic version wraps retrieval in a workflow that decides *what to do next*.

## Status

Early stage. Implemented: the Postgres-backed API, OpenSearch keyword and semantic (k-NN) search, hybrid RRF retrieval, and LLM answer generation via OpenRouter. Real-world arXiv ingestion is planned (see `Documentation/INGESTION_PLAN.md`); the agentic workflow is on the roadmap.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with the engine running)
- [uv](https://docs.astral.sh/uv/) (Python 3.12 is managed by uv)
- An [OpenRouter](https://openrouter.ai/) API key (required by `/ask`)

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
| `hybrid_search.py`   | RRF fusion of BM25 and k-NN results                              |
| `rag_pipeline.py`    | Builds RAG context/prompt and generates answers                 |
| `llm_client.py`      | OpenRouter client (Nemotron)                                     |
| `chunking.py`        | Text chunking helper for future passage-level retrieval         |

## API

| Method | Route               | Description                                              |
| ------ | ------------------- | -------------------------------------------------------- |
| GET    | `/health`           | Liveness probe                                           |
| GET    | `/papers`           | List all papers from Postgres                            |
| GET    | `/search?q=`        | Case-insensitive title search in Postgres (`ILIKE`)      |
| GET    | `/search/advanced`  | OpenSearch full-text search (`q`, `year`, `page`, `page_size`) |
| GET    | `/search/hybrid`    | Hybrid BM25 + k-NN search with RRF fusion (`q`, `limit`) |
| POST   | `/ask`              | Generate a grounded answer from retrieved papers; JSON body `{"question": "..."}` |

Examples:

```
http://127.0.0.1:8000/search/advanced?q=medical&year=2025
http://127.0.0.1:8000/search/hybrid?q=retrieval augmented generation&limit=3
```

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask `
  -ContentType 'application/json' `
  -Body '{"question": "What are the symptoms of a heart attack?"}'
```

## Testing

```powershell
docker compose up -d
uv run pytest -v
```

The tests hit the real Postgres and OpenSearch services, so both containers must be running. `.env` must contain `OPENROUTER_API_KEY` because the LLM client is imported at startup; the actual LLM calls are mocked in tests.
