
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_papers():
    response = client.get("/papers")

    assert response.status_code == 200

    data = response.json()
    assert len(data["papers"]) == 4
    assert data["papers"][0]["year"] == 2025


def test_search_papers():
    response = client.get("/search", params={"q": "medical"})

    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "medical"
    assert len(data["results"]) == 2


def test_search_is_case_insensitive():
    response = client.get("/search", params={"q": "RAG"})

    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_empty_search_is_rejected():
    response = client.get("/search", params={"q": ""})

    assert response.status_code == 422
