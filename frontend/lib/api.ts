const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

if (!process.env.NEXT_PUBLIC_API_URL && process.env.NODE_ENV === "production") {
  console.warn("NEXT_PUBLIC_API_URL is not set — API calls will fail in production.");
}

export interface SourceChunk {
  content: string;
  source: string;
  chunk_index: number;
  relevance_score: number | null;
}

export interface AskResponse {
  answer: string;
  sources: SourceChunk[];
  expanded_queries: string[];
  trace_id: string;
  latency_ms: number;
}

export interface QueryTrace {
  trace_id: string;
  timestamp: string;
  question: string;
  k: number;
  expanded_queries: string[];
  retrieved_chunks: SourceChunk[];
  answer: string;
  latency_ms: number;
}

export interface TraceListResponse {
  traces: QueryTrace[];
  total: number;
}

export async function askQuestion(
  question: string,
  k = 4
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, k }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchTraces(limit = 20): Promise<TraceListResponse> {
  const res = await fetch(`${API_BASE}/traces?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch traces: ${res.status}`);
  return res.json();
}

export async function fetchTrace(id: string): Promise<QueryTrace> {
  const res = await fetch(`${API_BASE}/traces/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Trace not found: ${res.status}`);
  return res.json();
}
