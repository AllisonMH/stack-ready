"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { askQuestion, AskResponse } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: AskResponse;
}

export default function AskPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [k, setK] = useState(4);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const response = await askQuestion(question, k);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.answer, response },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col max-w-3xl w-full mx-auto px-4">
      {/* Chat history */}
      <div className="flex-1 py-8 space-y-6 overflow-y-auto">
        {messages.length === 0 && (
          <div className="text-center mt-20">
            <p className="text-2xl font-semibold text-brand-accent mb-2">Ask an interview question</p>
            <p className="text-sm text-brand-soft/60">Answers are grounded in your full-stack developer study guide.</p>
            <div className="mt-6 flex flex-wrap gap-2 justify-center">
              {[
                "What is Big O notation?",
                "Explain REST vs GraphQL",
                "What are React hooks?",
                "How does CSS flexbox work?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-xs px-3 py-1.5 rounded-full border border-brand-primary text-brand-soft/70 hover:border-brand-secondary hover:text-brand-accent transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "flex justify-end" : ""}>
            {msg.role === "user" ? (
              <div className="bg-brand-primary rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-[80%] text-sm text-brand-accent">
                {msg.content}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-sm leading-relaxed whitespace-pre-wrap text-zinc-200">{msg.content}</div>

                {msg.response && (
                  <details className="group">
                    <summary className="cursor-pointer text-xs text-brand-secondary/60 hover:text-brand-secondary transition-colors list-none flex items-center gap-1.5">
                      <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
                      {msg.response.sources.length} chunks · {Math.round(msg.response.latency_ms)}ms ·{" "}
                      <Link
                        href={`/traces/${msg.response.trace_id}`}
                        className="underline underline-offset-2 hover:text-brand-accent"
                      >
                        trace
                      </Link>
                    </summary>

                    <div className="mt-3 space-y-3">
                      {/* Expanded queries */}
                      <div className="rounded-lg border border-brand-primary/50 bg-brand-primary/10 p-3">
                        <p className="text-xs font-medium text-brand-soft mb-2">Query expansions</p>
                        <ul className="space-y-1">
                          {msg.response.expanded_queries.map((q, j) => (
                            <li key={j} className="text-xs text-brand-soft/60 flex gap-2">
                              <span className="text-brand-secondary/40 shrink-0">{j + 1}.</span>
                              {q}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Source chunks */}
                      <div className="space-y-2">
                        {msg.response.sources.map((chunk, j) => (
                          <div key={j} className="rounded-lg border border-brand-primary/40 p-3">
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-xs text-brand-secondary/60">chunk #{chunk.chunk_index}</span>
                              {chunk.relevance_score != null && (
                                <span className="text-xs font-mono text-brand-soft/60">
                                  score {chunk.relevance_score.toFixed(3)}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-zinc-400 leading-relaxed line-clamp-4">
                              {chunk.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </details>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="text-brand-secondary text-sm animate-pulse">Thinking…</div>
        )}
        {error && (
          <div className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded-lg px-4 py-2.5">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="py-4 border-t border-brand-primary/40">
        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Ask an interview question… (Enter to send)"
              rows={1}
              className="w-full bg-brand-primary/10 border border-brand-primary/50 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder:text-brand-soft/30 focus:outline-none focus:border-brand-secondary resize-none transition-colors"
            />
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <label className="text-xs text-brand-soft/50 whitespace-nowrap">
              k=
              <select
                value={k}
                onChange={(e) => setK(Number(e.target.value))}
                className="bg-brand-primary/20 border border-brand-primary/50 rounded px-1 py-0.5 ml-1 text-brand-accent focus:outline-none"
              >
                {[2, 3, 4, 6, 8, 10].map((n) => (
                  <option key={n} value={n}>{n}</option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-brand-secondary text-white rounded-xl px-4 py-3 text-sm font-medium hover:bg-brand-accent hover:text-brand-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Ask
            </button>
          </div>
        </form>
      </div>
      {/* Footer */}
      <div className="text-center pb-4">
        <p className="text-xs text-zinc-600">
          Created with 💜 by{" "}
          <a
            href="https://www.kolorkodedenterprises.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-zinc-400 transition-colors underline underline-offset-2"
          >
            Kolor Koded Enterprises
          </a>
        </p>
      </div>
    </div>
  );
}
