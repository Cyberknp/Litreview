from fastapi.testclient import TestClient
from main import app
import main

client = TestClient(app)


def test_ask_endpoint(monkeypatch):
    def fake_answer_question(question):
        return {
            "question": question,
            "answer": "Example answer.",
            "sources": [
                {
                    "paper_id": "1",
                    "title": "Example research paper",
                }
            ],
        }

    monkeypatch.setattr(
        main,
        "answer_question",
        fake_answer_question,
    )

    response = client.post(
        "/ask",
        json={
            "question": "What is a heart attack?"
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Example answer."
    assert len(response.json()["sources"]) == 1


def test_ask_rejects_short_question():
    response = client.post(
        "/ask",
        json={"question": "Hi"},
    )

    assert response.status_code == 422