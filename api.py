import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from agent import ask
from models import QuestionRequest, QuestionResponse, TraceListResponse, QueryTrace
from observability import Timer, new_trace_id, record_trace, get_traces, get_trace, logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Interview prep RAG API starting up")
    yield
    logger.info("Interview prep RAG API shutting down")


app = FastAPI(
    title="StackReady: The Interview Prep RAG Agent",
    description="Q&A assistant over a full-stack developer study guide with chunk inspection and query tracing.",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    """Ask an interview prep question. Returns the answer, source chunks, and a trace ID."""
    trace_id = new_trace_id()
    logger.info("incoming question | trace_id=%s question=%r", trace_id, request.question[:80])

    with Timer() as t:
        try:
            answer, chunks, expanded_queries = ask(request.question, k=request.k)
        except Exception as e:
            logger.exception("agent error | trace_id=%s", trace_id)
            raise HTTPException(status_code=500, detail=str(e))

    record_trace(
        trace_id=trace_id,
        question=request.question,
        k=request.k,
        expanded_queries=expanded_queries,
        retrieved_chunks=chunks,
        answer=answer,
        latency_ms=t.elapsed_ms,
    )

    return QuestionResponse(
        answer=answer,
        sources=chunks,
        expanded_queries=expanded_queries,
        trace_id=trace_id,
        latency_ms=t.elapsed_ms,
    )


@app.get("/traces", response_model=TraceListResponse)
def list_traces(limit: int = Query(default=20, ge=1, le=100)):
    """Return the most recent query traces (newest first)."""
    traces = get_traces(limit=limit)
    return TraceListResponse(traces=traces, total=len(traces))


@app.get("/traces/{trace_id}", response_model=QueryTrace)
def get_single_trace(trace_id: str):
    """Return a single trace by ID, including all retrieved chunks and scores."""
    trace = get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id!r} not found")
    return trace


@app.get("/health")
def health():
    return {"status": "ok"}
