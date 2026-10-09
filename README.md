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

Early stage. Core RAG pipeline under development; agentic workflow is on the roadmap.

## Roadmap

- [ ] Paper fetching (arXiv)
- [ ] Text extraction + metadata storage
- [ ] Keyword + semantic search
- [ ] Passage retrieval + answer generation with citations
- [ ] Tracing, caching, evaluation
- [ ] Agentic loop (re-search / rewrite / reject)
