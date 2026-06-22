import Link from "next/link";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <div className="space-y-6">
        <div className="space-y-3">
          <p className="text-sm font-medium uppercase tracking-wide text-zinc-500">
            Compliance RAG
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900">
            GDPR Compliance Agent
          </h1>
          <p className="text-lg leading-8 text-zinc-600">
            An agentic retrieval system for EU regulation Q&amp;A and obligation-driven document
            audits. Ask grounded questions with cited answers, or upload a contract to see where it
            meets — or misses — GDPR requirements.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link
            href="/ask"
            className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <h2 className="mb-2 text-lg font-semibold text-zinc-900">Ask</h2>
            <p className="text-sm leading-6 text-zinc-600">
              Query ingested regulations with an agent that retrieves, grades relevance, and
              generates cited answers.
            </p>
          </Link>

          <Link
            href="/audit"
            className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
          >
            <h2 className="mb-2 text-lg font-semibold text-zinc-900">Audit</h2>
            <p className="text-sm leading-6 text-zinc-600">
              Upload an employment contract or policy document and receive a severity-ranked GDPR
              compliance report.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
