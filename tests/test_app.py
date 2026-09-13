import os
import tempfile

import pytest

import app as chatbot


@pytest.fixture()
def client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr(chatbot, "DB_PATH", db_path)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    chatbot.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    chatbot.init_db()

    with chatbot.app.test_client() as test_client:
        yield test_client

    os.unlink(db_path)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_create_conversation(client):
    response = client.post("/api/conversations", json={"visitor_name": "Demo Client"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["conversation_id"] > 0
    assert data["visitor_name"] == "Demo Client"


def test_chat_mock_provider(client):
    conversation = client.post("/api/conversations", json={"visitor_name": "Client"}).get_json()
    response = client.post(
        "/api/chat",
        json={"conversation_id": conversation["conversation_id"], "message": "Care este programul?"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["provider"] == "mock"
    assert "Luni" in data["reply"]


def test_chat_requires_message(client):
    conversation = client.post("/api/conversations", json={}).get_json()
    response = client.post("/api/chat", json={"conversation_id": conversation["conversation_id"]})
    assert response.status_code == 400


def test_unknown_conversation(client):
    response = client.get("/api/conversations/999999/messages")
    assert response.status_code == 404
