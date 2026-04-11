import Link from "next/link";
import { fetchTraces } from "@/lib/api";

export default async function TracesPage() {
  let data;
  try {
    data = await fetchTraces(50);
  } catch {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-red-400 text-sm">
        Could not connect to the API. Make sure the backend is running on port 8000.
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 w-full">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-lg font-semibold text-brand-accent">Query Traces</h1>
        <span className="text-sm text-brand-soft/50">{data.total} recorded</span>
      </div>

      {data.traces.length === 0 ? (
        <p className="text-brand-soft/50 text-sm">
          No traces yet.{" "}
          <Link href="/" className="text-brand-secondary underline underline-offset-2 hover:text-brand-accent">
            Ask a question
          </Link>{" "}
          to get started.
        </p>
      ) : (
        <div className="space-y-2">
          {data.traces.map((trace) => (
            <Link
              key={trace.trace_id}
              href={`/traces/${trace.trace_id}`}
              className="block rounded-xl border border-brand-primary/40 bg-brand-primary/5 p-4 hover:border-brand-secondary/60 hover:bg-brand-primary/15 transition-colors group"
            >
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm text-zinc-300 group-hover:text-brand-accent transition-colors line-clamp-1 flex-1">
                  {trace.question}
                </p>
                <span className="text-xs font-mono text-brand-soft/40 shrink-0">
                  {Math.round(trace.latency_ms)}ms
                </span>
              </div>
              <div className="mt-1.5 flex gap-3 text-xs text-brand-secondary/40">
                <span>{trace.retrieved_chunks.length} chunks</span>
                <span>{trace.expanded_queries.length} expansions</span>
                <span>{new Date(trace.timestamp).toLocaleString()}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
