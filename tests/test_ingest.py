import ingest


def test_ingest_updates_existing_documents(monkeypatch):
    sample_papers = [
        {
            "id": 5,
            "title": "Updated AI Research",
            "year": 2026,
            "abstract": "Updated abstract",
        }
    ]

    captured_actions = []

    monkeypatch.setattr(
        ingest,
        "fetch_papers",
        lambda: sample_papers,
    )

    monkeypatch.setattr(
        ingest,
        "embed_text",
        lambda text: [0.1] * 384,
    )

    def fake_bulk(client, actions, **kwargs):
        captured_actions.extend(actions)
        return len(actions), []

    monkeypatch.setattr(ingest, "bulk", fake_bulk)

    ingest.ingest_papers()

    assert len(captured_actions) == 1
    assert captured_actions[0]["_id"] == "5"
    assert captured_actions[0]["_source"]["title"] == "Updated AI Research"
    assert len(captured_actions[0]["_source"]["text_vector"]) == 384