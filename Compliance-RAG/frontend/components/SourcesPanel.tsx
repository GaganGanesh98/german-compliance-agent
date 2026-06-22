"use client";

import { useState } from "react";

import type { QueryResponse } from "@/lib/api";

interface SourcesPanelProps {
  response: QueryResponse;
}

export function SourcesPanel({ response }: SourcesPanelProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-zinc-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-zinc-800"
      >
        <span>Sources &amp; agent trace</span>
        <span className="text-zinc-400">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="space-y-6 border-t border-zinc-200 px-4 py-4">
          {response.trace.length > 0 && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Agent trace
              </h3>
              <ol className="flex flex-wrap items-center gap-2">
                {response.trace.map((step, index) => (
                  <li key={`${step}-${index}`} className="flex items-center gap-2">
                    <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                      {step}
                    </span>
                    {index < response.trace.length - 1 && (
                      <span className="text-zinc-300">→</span>
                    )}
                  </li>
                ))}
              </ol>
              <p className="mt-2 text-xs text-zinc-500">
                Retrieval rewrites: {response.retrieval_tries} · Generation retries:{" "}
                {response.generation_tries}
              </p>
            </section>
          )}

          <section>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-zinc-500">
              Retrieved documents
            </h3>
            {response.documents.length === 0 ? (
              <p className="text-sm text-zinc-500">No documents retrieved.</p>
            ) : (
              <ul className="space-y-3">
                {response.documents.map((doc, index) => (
                  <li
                    key={`${doc.article_ref ?? "doc"}-${index}`}
                    className="rounded-md border border-zinc-100 bg-zinc-50 p-3"
                  >
                    <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-zinc-600">
                      <span className="font-medium">
                        {doc.regulation_code ?? "N/A"} · {doc.article_ref ?? "N/A"}
                      </span>
                      <span className="rounded bg-white px-1.5 py-0.5 ring-1 ring-zinc-200">
                        {(doc.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed text-zinc-700">
                      {doc.content.length > 400
                        ? `${doc.content.slice(0, 400)}…`
                        : doc.content}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
