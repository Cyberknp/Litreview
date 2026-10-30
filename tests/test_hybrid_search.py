
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_hybrid_search_returns_results():
    response = client.get(
        "/search/hybrid",
        params={"q": "medical diagnosis"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "medical diagnosis"
    assert data["count"] >= 1


def test_hybrid_search_includes_rank_information():
    response = client.get(
        "/search/hybrid",
        params={"q": "heart attack"},
    )

    assert response.status_code == 200

    results = response.json()["results"]
    assert len(results) >= 1

    for paper in results:
        assert "rrf_score" in paper
        assert (
            paper["bm25_rank"] is not None
            or paper["semantic_rank"] is not None
        )


def test_hybrid_search_rejects_empty_query():
    response = client.get(
        "/search/hybrid",
        params={"q": ""},
    )

    assert response.status_code == 422
