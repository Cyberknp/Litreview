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

Early stage. The Postgres-backed API and OpenSearch full-text search are implemented; semantic search, LLM answer generation, and the agentic workflow are on the roadmap.

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with the engine running)
- [uv](https://docs.astral.sh/uv/) (Python 3.12 is managed by uv)

## Setup

```powershell
uv sync                        # install dependencies into .venv
docker compose up -d           # start Postgres and OpenSearch
uv run python .\init_db.py     # create tables and seed sample papers (Postgres)
uv run python .\search_engine.py  # create the OpenSearch index and seed sample papers
uv run uvicorn main:app --reload  # start the API at http://127.0.0.1:8000
```

## Services

| Service    | Host port | Notes                                                        |
| ---------- | --------- | ------------------------------------------------------------ |
| API        | `8000`    | FastAPI, interactive docs at `/docs`                         |
| Postgres   | `5433`    | Mapped to container port 5432 to avoid the native Windows PostgreSQL service |
| OpenSearch | `9200`    | Security plugin disabled for local development               |

Database connection defaults to `postgresql://rag_user:local_dev_password@localhost:5433/papers_db` and can be overridden with the `DATABASE_URL` environment variable.

## API

| Method | Route               | Description                                              |
| ------ | ------------------- | -------------------------------------------------------- |
| GET    | `/health`           | Liveness probe                                           |
| GET    | `/papers`           | List all papers from Postgres                            |
| GET    | `/search?q=`        | Case-insensitive title search in Postgres (`ILIKE`)      |
| GET    | `/search/advanced`  | OpenSearch full-text search (`q`, `year`, `page`, `page_size`) |

Example: `http://127.0.0.1:8000/search/advanced?q=medical&year=2025`

## Testing

```powershell
docker compose up -d
uv run pytest -v
```

The tests hit the real Postgres and OpenSearch services, so both containers must be running.
