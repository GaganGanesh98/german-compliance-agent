"use client";

import { useState } from "react";

import { AuditReportView } from "@/components/AuditReportView";
import { ApiError, runAudit, type AuditReport } from "@/lib/api";

export function AuditUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AuditReport | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }

    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const result = await runAudit(file);
      setReport(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status
            ? `Audit failed (${err.message}). Is the backend running on port 8000?`
            : err.message,
        );
      } else if (err instanceof TypeError) {
        setError(
          "Could not reach the compliance API. Start the backend with uvicorn app.api:app --reload.",
        );
      } else {
        setError("Something went wrong while running the audit.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="audit-file" className="mb-2 block text-sm font-medium text-zinc-700">
            Upload document
          </label>
          <input
            id="audit-file"
            type="file"
            accept=".pdf,.txt"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            className="block w-full text-sm text-zinc-700 file:mr-4 file:rounded-md file:border-0 file:bg-zinc-100 file:px-4 file:py-2 file:text-sm file:font-medium file:text-zinc-700 hover:file:bg-zinc-200"
          />
          <p className="mt-2 text-xs text-zinc-500">Accepted formats: PDF or plain text.</p>
        </div>

        <button
          type="submit"
          disabled={loading || !file}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-700 disabled:cursor-not-allowed disabled:bg-zinc-400"
        >
          {loading ? "Auditing against GDPR…" : "Run audit"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-3 rounded-lg border border-zinc-200 bg-white px-4 py-8 text-sm text-zinc-600">
          <span className="inline-block h-5 w-5 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-700" />
          Auditing against GDPR… This usually takes 10–30 seconds.
        </div>
      )}

      {report && !loading && <AuditReportView report={report} />}
    </div>
  );
}
