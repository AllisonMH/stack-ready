import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api import app
from models import SourceChunk
from observability import _trace_store


MOCK_CHUNK = SourceChunk(
    content="Big O notation describes algorithm time complexity.",
    source="study-guide.txt",
    chunk_index=42,
    relevance_score=0.91,
)

MOCK_ASK_RETURN = (
    "Big O notation is a way to describe algorithm efficiency.",
    [MOCK_CHUNK],
    ["How is time complexity measured?", "Explain algorithmic efficiency"],
)


@pytest.fixture(autouse=True)
def clear_traces():
    _trace_store.clear()
    yield
    _trace_store.clear()


@pytest.fixture
def client():
    return TestClient(app)


# --- /health ---

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- POST /ask ---

def test_ask_success(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN):
        resp = client.post("/ask", json={"question": "What is Big O notation?"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == MOCK_ASK_RETURN[0]
    assert len(body["sources"]) == 1
    assert body["sources"][0]["chunk_index"] == 42
    assert len(body["expanded_queries"]) == 2
    assert "trace_id" in body
    assert body["latency_ms"] >= 0


def test_ask_creates_trace(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN):
        resp = client.post("/ask", json={"question": "What is Big O notation?"})

    trace_id = resp.json()["trace_id"]
    trace_resp = client.get(f"/traces/{trace_id}")
    assert trace_resp.status_code == 200
    assert trace_resp.json()["question"] == "What is Big O notation?"


def test_ask_default_k(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN) as mock_ask:
        client.post("/ask", json={"question": "test"})
        _, kwargs = mock_ask.call_args
        assert kwargs.get("k", mock_ask.call_args[0][1] if len(mock_ask.call_args[0]) > 1 else 4) == 4


def test_ask_custom_k(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN) as mock_ask:
        client.post("/ask", json={"question": "test", "k": 6})
        args, kwargs = mock_ask.call_args
        k_value = kwargs.get("k") or args[1]
        assert k_value == 6


def test_ask_invalid_k_too_high(client):
    resp = client.post("/ask", json={"question": "test", "k": 11})
    assert resp.status_code == 422


def test_ask_invalid_k_zero(client):
    resp = client.post("/ask", json={"question": "test", "k": 0})
    assert resp.status_code == 422


def test_ask_missing_question(client):
    resp = client.post("/ask", json={})
    assert resp.status_code == 422


def test_ask_agent_error_returns_500(client):
    with patch("api.ask", side_effect=RuntimeError("Chroma unavailable")):
        resp = client.post("/ask", json={"question": "What is REST?"})
    assert resp.status_code == 500
    assert "Chroma unavailable" in resp.json()["detail"]


# --- GET /traces ---

def test_list_traces_empty(client):
    resp = client.get("/traces")
    assert resp.status_code == 200
    body = resp.json()
    assert body["traces"] == []
    assert body["total"] == 0


def test_list_traces_after_ask(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN):
        client.post("/ask", json={"question": "Q1"})
        client.post("/ask", json={"question": "Q2"})

    resp = client.get("/traces")
    body = resp.json()
    assert body["total"] == 2
    # Newest first
    assert body["traces"][0]["question"] == "Q2"
    assert body["traces"][1]["question"] == "Q1"


def test_list_traces_limit(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN):
        for i in range(5):
            client.post("/ask", json={"question": f"Q{i}"})

    resp = client.get("/traces?limit=3")
    assert len(resp.json()["traces"]) == 3


# --- GET /traces/{trace_id} ---

def test_get_trace_not_found(client):
    resp = client.get("/traces/nonexistent-id")
    assert resp.status_code == 404


def test_get_trace_detail(client):
    with patch("api.ask", return_value=MOCK_ASK_RETURN):
        ask_resp = client.post("/ask", json={"question": "What is Big O?"})

    trace_id = ask_resp.json()["trace_id"]
    resp = client.get(f"/traces/{trace_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace_id"] == trace_id
    assert body["answer"] == MOCK_ASK_RETURN[0]
    assert len(body["retrieved_chunks"]) == 1
    assert body["retrieved_chunks"][0]["relevance_score"] == 0.91
    assert len(body["expanded_queries"]) == 2
