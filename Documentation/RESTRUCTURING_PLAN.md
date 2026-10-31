# Directory Restructuring Plan

Status: Proposed
Scope: Project layout, module boundaries, configuration consolidation, and repo hygiene for the Litreview codebase.

## Current state

Flat root with 10 Python modules, one empty file, and two capitalized single-file folders:

```
Litreview/
├── chunking.py  chunk_ingest.py (0 bytes)  db.py  hybrid_search.py
├── ingest.py  init_db.py  llm_client.py  main.py  rag_pipeline.py
├── search_engine.py  semantic_search.py
├── tests/ (6 files, mixed naming)
├── Documentation/INGESTION_PLAN.md
├── Frontend/masterprompt.txt
├── Compose.yaml  pyproject.toml  uv.lock  README.md  LICENSE  NOTICE
├── .env (.gitignored)  .env.example  .gitignore  .python-version
```

## Problems this creates

1. **Import tangle** — `main.py` imports 4 root modules; `hybrid_search` → `semantic_search`; `rag_pipeline` → `hybrid_search` + `llm_client`; tests import bare `main`, `ingest`, `chunking`. Any rename ripples everywhere with no package boundaries.
2. **Duplicated infrastructure** — two independent OpenSearch clients (`semantic_search.py:5`, `search_engine.py:5`), three hardcoded index names, and the same 4 sample papers copied in `db.py`, `semantic_search.py`, `search_engine.py`.
3. **Scattered config** — `DATABASE_URL` read in `db.py`, `.env` loaded only in `llm_client.py`, model name + dims + RRF constant hardcoded per module.
4. **Heavy import side effects** — `semantic_search.py:16` loads the SentenceTransformer at import time; because `main.py` → rag → hybrid → semantic, every API/test startup pays ~10s and downloads weights.
5. **Scripts mixed with app code** — `init_db.py`, `ingest.py`, `search_engine.py` are operational scripts living beside importable modules.
6. **Hygiene** — empty `chunk_ingest.py`; `test_advanced_Search.py` violates snake_case; integration tests are indistinguishable from unit tests; `Documentation/` and `Frontend/` capitalized single-file folders; `Compose.yaml` capitalized; no lint/format/CI config; `pyproject` description is still the template placeholder.

## Proposed target structure (recommended: `app/` package)

```
Litreview/
├── app/
│   ├── __init__.py
│   ├── main.py                 # create_app(), router includes only
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py           # GET /health
│   │   ├── papers.py           # GET /papers, GET /search (Postgres)
│   │   ├── search.py           # GET /search/advanced, /search/hybrid
│   │   └── ask.py              # POST /ask
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # load_dotenv() once; all env + index names
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py       # get_connection()
│   │   ├── schema.py           # DDL + migrations (initialize_database)
│   │   └── queries.py          # list_papers, search_titles, upsert_papers
│   ├── search/
│   │   ├── __init__.py
│   │   ├── client.py           # single OpenSearch client
│   │   ├── keyword.py          # search_engine.py
│   │   ├── semantic.py         # get_model()/embed_text/semantic_search
│   │   └── hybrid.py           # RRF fusion
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chunking.py
│   │   ├── pipeline.py         # build_context/build_prompt/answer_question
│   │   └── llm.py              # OpenRouter client
│   └── ingestion/
│       ├── __init__.py
│       ├── service.py          # ingest.py (Postgres → embeddings → OpenSearch)
│       └── chunks.py           # to replace empty chunk_ingest.py
├── scripts/
│   ├── __init__.py
│   ├── init_db.py              # thin wrapper → app.db.schema
│   ├── seed_indexes.py         # keyword + semantic index creation/seed
│   └── ingest.py               # thin wrapper → app.ingestion.service
├── tests/
│   ├── conftest.py             # TestClient + service-availability fixtures
│   ├── unit/                   # chunking, RRF fusion, parsers (offline)
│   ├── integration/            # db, ingest, keyword/semantic search
│   └── api/                    # route tests (main, ask, hybrid)
├── docs/
│   ├── INGESTION_PLAN.md
│   └── frontend-welcome-brief.md   # from Frontend/masterprompt.txt
├── frontend/                   # reserved for the real UI (optional now)
├── compose.yaml                # renamed from Compose.yaml
├── pyproject.toml  uv.lock  README.md  LICENSE  NOTICE
├── .env.example  .gitignore  .python-version
```

This keeps `uv run` workflows simple (`uv run uvicorn app.main:app`), avoids packaging setup, and makes the dependency graph explicit: `api → rag/search/db`, `rag → search + llm`, `search → client/config`.

## File mapping

| Today | Target |
| --- | --- |
| `main.py` | `app/main.py` + split routes into `app/api/*` |
| `db.py` | `app/db/connection.py`, `schema.py`, `queries.py` |
| `init_db.py` | `scripts/init_db.py` |
| `semantic_search.py` | `app/search/semantic.py` (lazy model) |
| `search_engine.py` | `app/search/keyword.py` + index setup → `scripts/seed_indexes.py` |
| `hybrid_search.py` | `app/search/hybrid.py` |
| `rag_pipeline.py` | `app/rag/pipeline.py` |
| `llm_client.py` | `app/rag/llm.py` |
| `chunking.py` | `app/rag/chunking.py` |
| `ingest.py` | `app/ingestion/service.py` |
| `chunk_ingest.py` (empty) | delete, or implement as `app/ingestion/chunks.py` |
| `tests/*.py` | split into `tests/unit`, `tests/integration`, `tests/api` |
| `Documentation/INGESTION_PLAN.md` | `docs/INGESTION_PLAN.md` |
| `Frontend/masterprompt.txt` | `docs/frontend-welcome-brief.md` (or `frontend/README.md`) |
| `Compose.yaml` | `compose.yaml` |

## Consolidations that come with the move

1. **`app/core/config.py`** — call `load_dotenv()` once; expose `DATABASE_URL`, `OPENROUTER_API_KEY/MODEL`, `EMBEDDING_MODEL`, `EMBEDDING_DIM = 384`, `INDEX_KEYWORD`, `INDEX_SEMANTIC`, `INDEX_CHUNKS`, `RRF_K`. Env-overridable, defaults keep the existing index names so no re-indexing is needed. Remove `load_dotenv` from `llm_client` and `os.getenv` from `db.py`.
2. **`app/search/client.py`** — one OpenSearch client with the current localhost:9200/no-SSL settings, imported by semantic/keyword/hybrid/ingest/chunks.
3. **One sample dataset** — move the 4-paper list into a fixture (`tests/fixtures/sample_papers.py`) or `app/ingestion/sample_data.py`; seeding scripts and tests consume it instead of three copies.
4. **Lazy embedding model** — `@lru_cache def get_model()`; keeps `import app.main` fast and tests ~10s quicker.
5. **CLI commands** — run as modules to keep `app` importable without packaging:

   ```powershell
   uv run python -m scripts.init_db
   uv run python -m scripts.seed_indexes
   uv run uvicorn app.main:app --reload
   ```

   (Alternative: add `[build-system]` + `[project.scripts]` entry points if installed commands are preferred.)

## Tests and repo hygiene

- Rename `test_advanced_Search.py` → `test_advanced_search.py`; move tests into `unit/`, `integration/`, `api/` with unique basenames (or `__init__.py` per folder).
- `conftest.py`: shared `TestClient`, plus a fixture that skips `integration` tests when Postgres/OpenSearch are unreachable; register `integration` marker in `pyproject` and add `testpaths = ["tests"]`.
- Keep `.env` ignored (already correct), `.env.example` tracked; delete empty `chunk_ingest.py`; `__pycache__`/`.pytest_cache` are already ignored — safe to delete locally.
- `pyproject.toml`: real description, add `[tool.ruff]` (target py312) and `ruff` to dev deps; optional pre-commit.
- Optional CI: GitHub Actions with Postgres 16 and `opensearchproject/opensearch:3.4.0` service containers, `uv sync --frozen`, `ruff check`, `pytest`.
- Update README's layout/commands after the move (it still documents the flat paths).
- Windows caveat: case-only git renames need two steps (`git mv Compose.yaml compose.tmp; git mv compose.tmp compose.yaml`).

## Migration order (low risk)

1. Create folders + `__init__.py`; `git mv` modules; fix imports to absolute `app.*`.
2. Add `core/config.py` + `search/client.py`; replace duplicated constants/clients; lazy-load the model.
3. Move scripts; update commands in README.
4. Reorganize tests; add markers/conftest; fix monkeypatch targets (`main.answer_question` → `app.api.ask.answer_question`, etc.).
5. Rename docs/folders; delete empty file; lint config.
6. Verify: `uv run pytest -v`, `uv run uvicorn app.main:app`, hit `/papers`, `/search/hybrid`, `/ask`; run both scripts.

## Open questions

1. Layout: `app/` package (recommended, minimal setup) or `src/litreview/` (better if the project will be packaged/published)?
2. Split `main.py` into `app/api/*` routers now, or keep a single `app/main.py` for fewer moving parts?
3. Keep current OpenSearch index names as defaults (no re-indexing) or normalize them now?
4. Include ruff/pre-commit/CI with this refactor, or folder moves only?
5. Should the empty `chunk_ingest.py` be deleted or scaffolded as `app/ingestion/chunks.py`?
