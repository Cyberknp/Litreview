from fastapi.testclient import TestClient
from main import app
import main

client = TestClient(app)


def test_chunk_ask_endpoint(monkeypatch):

    def fake_answer(question):
        return {
            "question": question,
            "answer": "AI can support clinical diagnosis.",
            "sources": [
                {
                    "paper_id": 5,
                    "chunk_id": 1,
                    "title": "AI in Clinical Diagnosis",
                    "chunk_text": "AI supports clinical decision-making.",
                }
            ],
        }

    monkeypatch.setattr(
        main,
        "answer_with_chunks",
        fake_answer,
    )

    response = client.post(
        "/ask/chunks",
        json={
            "question": "How does AI support diagnosis?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "answer" in data
    assert data["sources"][0]["paper_id"] == 5
    assert data["sources"][0]["chunk_id"] == 1


def test_chunk_ask_rejects_short_question():

    response = client.post(
        "/ask/chunks",
        json={"question": "Hi"},
    )

    assert response.status_code == 422