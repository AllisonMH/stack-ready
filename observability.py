import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Optional
import uuid

from models import QueryTrace, SourceChunk

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag")

# In-memory ring buffer — keeps the last 100 traces
_trace_store: deque[QueryTrace] = deque(maxlen=100)


def new_trace_id() -> str:
    return str(uuid.uuid4())


def record_trace(
    trace_id: str,
    question: str,
    k: int,
    expanded_queries: list[str],
    retrieved_chunks: list[SourceChunk],
    answer: str,
    latency_ms: float,
) -> QueryTrace:
    trace = QueryTrace(
        trace_id=trace_id,
        timestamp=datetime.now(timezone.utc),
        question=question,
        k=k,
        expanded_queries=expanded_queries,
        retrieved_chunks=retrieved_chunks,
        answer=answer,
        latency_ms=latency_ms,
    )
    _trace_store.append(trace)
    logger.info(
        "query completed | trace_id=%s latency_ms=%.1f chunks=%d expansions=%d question=%r",
        trace_id,
        latency_ms,
        len(retrieved_chunks),
        len(expanded_queries),
        question[:80],
    )
    return trace


def get_traces(limit: int = 20) -> list[QueryTrace]:
    traces = list(_trace_store)
    return list(reversed(traces))[:limit]


def get_trace(trace_id: str) -> Optional[QueryTrace]:
    for trace in _trace_store:
        if trace.trace_id == trace_id:
            return trace
    return None


class Timer:
    """Context manager that measures elapsed milliseconds."""

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000
