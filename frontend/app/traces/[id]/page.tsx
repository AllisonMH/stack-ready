import Link from "next/link";
import { fetchTrace } from "@/lib/api";

export default async function TracePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let trace;
  try {
    trace = await fetchTrace(id);
  } catch {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 text-sm text-brand-soft/50">
        <p className="text-red-400 mb-4">Trace not found or backend unavailable.</p>
        <Link href="/traces" className="text-brand-secondary underline underline-offset-2 hover:text-brand-accent">
          ← Back to traces
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 w-full space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/traces"
          className="text-xs text-brand-secondary/60 hover:text-brand-secondary transition-colors"
        >
          ← Traces
        </Link>
        <h1 className="mt-3 text-base font-semibold text-brand-accent">{trace.question}</h1>
        <div className="mt-1 flex gap-4 text-xs text-brand-soft/40">
          <span>{new Date(trace.timestamp).toLocaleString()}</span>
          <span>{Math.round(trace.latency_ms)}ms</span>
          <span>k={trace.k}</span>
          <span className="font-mono text-brand-primary/60">{trace.trace_id}</span>
        </div>
      </div>

      {/* Answer */}
      <section>
        <h2 className="text-xs font-medium text-brand-secondary/60 uppercase tracking-wider mb-3">Answer</h2>
        <p className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">{trace.answer}</p>
      </section>

      {/* Query expansions */}
      <section>
        <h2 className="text-xs font-medium text-brand-secondary/60 uppercase tracking-wider mb-3">
          Query Expansions
        </h2>
        <ol className="space-y-1.5">
          <li className="flex gap-3 text-sm">
            <span className="text-brand-secondary/40 shrink-0 w-4">0.</span>
            <span className="text-brand-soft">{trace.question}</span>
            <span className="text-brand-secondary/30 text-xs self-center">(original)</span>
          </li>
          {trace.expanded_queries.map((q, i) => (
            <li key={i} className="flex gap-3 text-sm">
              <span className="text-brand-secondary/40 shrink-0 w-4">{i + 1}.</span>
              <span className="text-brand-soft/60">{q}</span>
            </li>
          ))}
        </ol>
      </section>

      {/* Retrieved chunks */}
      <section>
        <h2 className="text-xs font-medium text-brand-secondary/60 uppercase tracking-wider mb-3">
          Retrieved Chunks ({trace.retrieved_chunks.length})
        </h2>
        <div className="space-y-3">
          {trace.retrieved_chunks.map((chunk, i) => (
            <div key={i} className="rounded-xl border border-brand-primary/40 bg-brand-primary/5 p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-brand-secondary/60">chunk #{chunk.chunk_index}</span>
                {chunk.relevance_score != null && (
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-20 rounded-full bg-brand-primary/30 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand-secondary"
                        style={{ width: `${Math.min(chunk.relevance_score * 100, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono text-brand-soft/60">
                      {chunk.relevance_score.toFixed(3)}
                    </span>
                  </div>
                )}
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed whitespace-pre-wrap">
                {chunk.content}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
