import pytest
from pydantic import ValidationError
from models import QuestionRequest, SourceChunk, QuestionResponse, QueryTrace, TraceListResponse
from datetime import datetime, timezone


def test_question_request_defaults():
    req = QuestionRequest(question="What is Big O?")
    assert req.k == 4


def test_question_request_custom_k():
    req = QuestionRequest(question="What is REST?", k=6)
    assert req.k == 6


def test_question_request_k_too_low():
    with pytest.raises(ValidationError):
        QuestionRequest(question="test", k=0)


def test_question_request_k_too_high():
    with pytest.raises(ValidationError):
        QuestionRequest(question="test", k=11)


def test_question_request_k_boundary_values():
    assert QuestionRequest(question="test", k=1).k == 1
    assert QuestionRequest(question="test", k=10).k == 10


def test_source_chunk_optional_score():
    chunk = SourceChunk(content="text", source="study-guide.txt", chunk_index=0)
    assert chunk.relevance_score is None


def test_source_chunk_with_score():
    chunk = SourceChunk(content="text", source="study-guide.txt", chunk_index=5, relevance_score=0.87)
    assert chunk.relevance_score == 0.87


def test_question_response_shape():
    chunk = SourceChunk(content="text", source="study-guide.txt", chunk_index=0, relevance_score=0.9)
    resp = QuestionResponse(
        answer="Big O is...",
        sources=[chunk],
        expanded_queries=["How is time complexity measured?"],
        trace_id="abc-123",
        latency_ms=500.0,
    )
    assert len(resp.sources) == 1
    assert len(resp.expanded_queries) == 1


def test_trace_list_response():
    result = TraceListResponse(traces=[], total=0)
    assert result.total == 0
    assert result.traces == []
