import { AuditUpload } from "@/components/AuditUpload";

export default function AuditPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8 space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Audit</h1>
        <p className="text-sm leading-6 text-zinc-600">
          Upload a PDF or text document to audit it against curated GDPR obligations. The report
          highlights violations, partial coverage, and gaps the document never addresses.
        </p>
      </div>
      <AuditUpload />
    </div>
  );
}
