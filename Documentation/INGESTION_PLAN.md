# Feature Plan: Real-World Data Ingestion (arXiv)

Status: Planned
Decisions: source = arXiv API, content = abstracts only, existing indexes and sample data stay as-is.

## Goal

Replace the hardcoded 4-paper sample corpus (in `semantic_search.py`, `search_engine.py`, and the `db.py` seed) with real research papers fetched from arXiv, so hybrid search and the RAG pipeline answer questions from actual literature.

The sample data is **not removed**: ingested papers are stored alongside it in the existing indexes.

## Architecture

```
arXiv API  ->  ingestion.py  ->  Postgres (source of truth, papers table)
                                     |
                                     v
                          OpenSearch (research-papers-semantic)
                          id/title/abstract/year + text_vector (384-dim)
                                     |
                                     v
                  hybrid_search.py / rag_pipeline.py (unchanged)
```

- arXiv Atom API is free and keyless: `https://export.arxiv.org/api/query`.
- Embeddings use the existing model (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) and the existing index mapping.
- Postgres stores full metadata; OpenSearch stores only the fields required for search.

## New file: `ingestion.py`

### Fetch

- `fetch_arxiv(query, max_results)` — `httpx` GET against the arXiv API:
  - params: `search_query=all:<query>`, `start`, `max_results` (max 100 per page, paginate for larger runs), `sortBy=relevance`
  - polite 3 second delay between pages; send a `User-Agent` header
- `parse_arxiv_feed(xml)` — parse with stdlib `xml.etree.ElementTree` (no new parser dependency):
  - `external_id` from the entry `id`
  - `title`, `abstract` (from `summary`), `year` (first 4 chars of `published`), `authors`, `url`
  - normalize whitespace (arXiv abstracts are multi-line)
  - skip entries with empty abstracts; dedupe by `external_id`

### Store

- Extend the `papers` table with idempotent migrations (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`):
  - `external_id TEXT UNIQUE`
  - `abstract TEXT`
  - `authors TEXT`
  - `url TEXT`
  - `source TEXT`
- Existing seed rows keep `external_id = NULL`; Postgres allows multiple NULLs in a unique index, so seed data is untouched.
- New `db.upsert_papers(papers)` using `ON CONFLICT (external_id) DO UPDATE ... RETURNING id, external_id`; re-ingesting the same query updates instead of duplicating.

### Embed and index

- Reuse `semantic_search.embed_text` and the existing mapping (`title/abstract/year` + `text_vector`).
- Embed `title + ". " + abstract`.
- Upsert each paper into `research-papers-semantic` with `_id` = Postgres integer `id`.
- Refresh the index at the end.

### CLI

```powershell
uv run python .\ingestion.py --query "retrieval augmented generation" --max 50
```

Prints counts for: fetched / skipped / upserted / indexed.

## Files touched

| File | Change |
| ---- | ------ |
| `ingestion.py` | New: fetch, parse, store, embed, index, CLI |
| `db.py` | Column migrations + `upsert_papers()` |
| `pyproject.toml` | `httpx` becomes a runtime dependency (`uv add httpx`) |
| `README.md` | Add "Ingesting real papers" section |
| `tests/test_ingestion.py` | New: offline parser tests with a saved Atom XML fixture |

No changes required to `main.py`, `hybrid_search.py`, or `rag_pipeline.py`; they query the same index and model.

## Testing

- `parse_arxiv_feed` tested against a checked-in Atom XML fixture: ids, titles, year extraction, whitespace normalization, empty-abstract skipping.
- No network calls in the test suite.
- Existing tests must stay green (`uv run pytest -q`).

## Verification

1. `uv run python .\ingestion.py --query "retrieval augmented generation" --max 10`
2. Re-run the same command: confirm 0 duplicates (idempotent).
3. `GET /search/hybrid?q=retrieval augmented generation` returns real arXiv titles.
4. `uv run pytest -q` passes.

## Caveats and limits

- arXiv politeness: ~1 request per 3 seconds; cap `--max` per run (e.g. 200).
- Titles/abstracts may contain LaTeX; stored and displayed as-is.
- Postgres and OpenSearch can drift if one write step fails; ingestion reports per-step counts so it can be safely re-run (idempotent).
- Free-tier infrastructure only; no paid APIs or keys required.

## Future extensions (out of scope)

- Full-text PDF download, chunking, and passage-level embeddings.
- Additional sources (OpenAlex, Semantic Scholar).
- Scheduled ingestion and incremental updates.
- Citation metadata (authors/venue) included in the RAG prompt context.
