"use client";

import { useEffect, useState } from "react";

import { AnswerWithCitations } from "@/components/AnswerWithCitations";
import { SourcesPanel } from "@/components/SourcesPanel";
import {
  ApiError,
  askQuestion,
  takePendingFollowUp,
  type QueryResponse,
} from "@/lib/api";

export function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [regulation, setRegulation] = useState<string>("GDPR");
  const [findingContext, setFindingContext] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<QueryResponse | null>(null);

  // Consume a pending "Ask a follow-up" handoff from the Audit page. Reading
  // clears sessionStorage, so a stale finding can't leak into a later unrelated
  // chat (e.g. a fresh /ask visit).
  useEffect(() => {
    const pending = takePendingFollowUp();
    if (!pending) {
      return;
    }
    /* eslint-disable react-hooks/set-state-in-effect --
       One-time hydration from sessionStorage, a per-tab browser store that is
       unavailable during SSR. A lazy useState initializer can't read it without a
       hydration mismatch, so the read must happen after mount. Runs once. */
    setQuestion(pending.question);
    setRegulation(pending.regulation);
    setFindingContext(pending.findingContext);
    /* eslint-enable react-hooks/set-state-in-effect */
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await askQuestion(
        trimmed,
        regulation === "ALL" ? null : regulation,
        findingContext,
      );
      // The finding context belongs to this prefilled follow-up only; drop it so
      // a subsequent, unrelated question in the same session doesn't carry it.
      setFindingContext(null);
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
        {findingContext && (
          <div className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-600">
            Following up on an audit finding — the finding&rsquo;s context is attached to your
            next question.
          </div>
        )}
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
