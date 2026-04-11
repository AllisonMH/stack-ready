import time
import pytest
from observability import Timer, record_trace, get_traces, get_trace, new_trace_id, _trace_store
from models import SourceChunk


@pytest.fixture(autouse=True)
def clear_trace_store():
    """Reset the in-memory trace store before each test."""
    _trace_store.clear()
    yield
    _trace_store.clear()


def _make_chunk(index: int = 0) -> SourceChunk:
    return SourceChunk(
        content="Some chunk content",
        source="study-guide.txt",
        chunk_index=index,
        relevance_score=0.85,
    )


def _record(question: str = "What is REST?", trace_id: str | None = None) -> str:
    tid = trace_id or new_trace_id()
    record_trace(
        trace_id=tid,
        question=question,
        k=4,
        expanded_queries=["How does REST work?", "Explain REST APIs"],
        retrieved_chunks=[_make_chunk()],
        answer="REST is an architectural style...",
        latency_ms=300.0,
    )
    return tid


# --- Timer ---

def test_timer_measures_elapsed():
    with Timer() as t:
        time.sleep(0.05)
    assert t.elapsed_ms >= 50
    assert t.elapsed_ms < 500


def test_timer_is_fast_without_sleep():
    with Timer() as t:
        pass
    assert t.elapsed_ms < 100


# --- record_trace / get_trace ---

def test_record_and_retrieve_trace():
    tid = _record()
    trace = get_trace(tid)
    assert trace is not None
    assert trace.trace_id == tid
    assert trace.question == "What is REST?"


def test_get_trace_missing_returns_none():
    assert get_trace("nonexistent-id") is None


def test_trace_stores_expanded_queries():
    tid = _record()
    trace = get_trace(tid)
    assert trace.expanded_queries == ["How does REST work?", "Explain REST APIs"]


def test_trace_stores_chunks():
    tid = _record()
    trace = get_trace(tid)
    assert len(trace.retrieved_chunks) == 1
    assert trace.retrieved_chunks[0].chunk_index == 0


# --- get_traces ---

def test_get_traces_newest_first():
    tid1 = _record("Question one")
    tid2 = _record("Question two")
    traces = get_traces()
    assert traces[0].trace_id == tid2
    assert traces[1].trace_id == tid1


def test_get_traces_respects_limit():
    for i in range(5):
        _record(f"Question {i}")
    assert len(get_traces(limit=3)) == 3


def test_get_traces_empty_store():
    assert get_traces() == []


def test_trace_store_ring_buffer(monkeypatch):
    """Store should evict oldest entries once maxlen (100) is reached."""
    import observability
    from collections import deque

    # Use a smaller maxlen to make the test fast
    small_store = deque(maxlen=3)
    monkeypatch.setattr(observability, "_trace_store", small_store)

    ids = [_record(f"Q{i}") for i in range(4)]
    # First entry should have been evicted
    assert get_trace(ids[0]) is None
    assert get_trace(ids[1]) is not None
