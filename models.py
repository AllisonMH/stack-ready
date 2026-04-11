from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class QuestionRequest(BaseModel):
    question: str
    k: int = Field(default=4, ge=1, le=10, description="Number of chunks to retrieve")


class SourceChunk(BaseModel):
    content: str
    source: str
    chunk_index: int
    relevance_score: Optional[float] = None


class QuestionResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    expanded_queries: list[str]
    trace_id: str
    latency_ms: float


class QueryTrace(BaseModel):
    trace_id: str
    timestamp: datetime
    question: str
    k: int
    expanded_queries: list[str]
    retrieved_chunks: list[SourceChunk]
    answer: str
    latency_ms: float


class TraceListResponse(BaseModel):
    traces: list[QueryTrace]
    total: int
