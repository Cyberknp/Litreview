from fastapi.testclient import TestClient

from main import app

client=TestClient(app)

def test_advanced_search_returns_results():
    response = client.get(
        "/search/advanced",
        params={"q": "medical"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["results"]) >= 1

def test_advanced_search_filters_by_year():
    response = client.get(
        "/search/advanced",
        params={"q": "medical", "year": 2025},
    )

    assert response.status_code == 200

    for paper in response.json()["results"]:
        assert paper["year"] == 2025

def test_advanced_search_validates_page_size():
    response = client.get(
        "/search/advanced",
        params={"q": "medical", "page_size": 0},
    )

    assert response.status_code == 422
