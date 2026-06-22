"use client";

import { useState } from "react";

import { AnswerWithCitations } from "@/components/AnswerWithCitations";
import { SourcesPanel } from "@/components/SourcesPanel";
import { ApiError, askQuestion, type QueryResponse } from "@/lib/api";

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [regulation, setRegulation] = useState<string>("GDPR");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await askQuestion(trimmed, regulation === "ALL" ? null : regulation);
      setResponse(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status
            ? `Could not reach the compliance API (${err.message}). Is the backend running on port 8000?`
            : err.message,
        );
      } else if (err instanceof TypeError) {
        setError(
          "Could not reach the compliance API. Start the backend with uvicorn app.api:app --reload.",
        );
      } else {
        setError("Something went wrong while fetching the answer.");
      }
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="question" className="mb-2 block text-sm font-medium text-zinc-700">
            Your question
          </label>
          <textarea
            id="question"
            rows={4}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="e.g. What is the lawful basis for processing personal data?"
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm outline-none ring-zinc-300 focus:ring-2"
          />
        </div>

        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="regulation" className="mb-2 block text-sm font-medium text-zinc-700">
              Regulation
            </label>
            <select
              id="regulation"
              value={regulation}
              onChange={(event) => setRegulation(event.target.value)}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 shadow-sm outline-none focus:ring-2 focus:ring-zinc-300"
            >
              <option value="GDPR">GDPR</option>
              <option value="ALL">All</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            {loading ? "Searching regulations…" : "Ask"}
          </button>
        </div>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-lg border border-zinc-200 bg-white px-4 py-8 text-center text-sm text-zinc-500">
          The agent is retrieving, grading, and generating an answer…
        </div>
      )}

      {response && !loading && (
        <div className="space-y-4">
          <div className="rounded-lg border border-zinc-200 bg-white p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
              Answer
            </h2>
            <AnswerWithCitations answer={response.answer} citations={response.citations} />
          </div>
          <SourcesPanel response={response} />
        </div>
      )}
    </div>
  );
}
