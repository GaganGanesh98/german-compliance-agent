import type { AuditReport } from "@/lib/api";

import { FindingCard } from "@/components/FindingCard";
import { StatusBadge } from "@/components/StatusBadge";

const STATUS_ORDER = ["VIOLATION", "NOT_ADDRESSED", "PARTIAL", "COMPLIANT"] as const;

interface AuditReportViewProps {
  report: AuditReport;
}

export function AuditReportView({ report }: AuditReportViewProps) {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight text-zinc-900">
          {report.document_title}
        </h2>
        <p className="text-sm text-zinc-500">
          Generated {new Date(report.generated_at).toLocaleString()}
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {STATUS_ORDER.map((status) => {
          const count = report.summary[status] ?? 0;
          if (count === 0) {
            return null;
          }
          return (
            <div
              key={status}
              className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-3 py-2"
            >
              <StatusBadge status={status} />
              <span className="text-sm font-medium text-zinc-700">{count}</span>
            </div>
          );
        })}
      </div>

      <div className="space-y-4">
        {report.findings.map((finding) => (
          <FindingCard key={finding.checkpoint_id} finding={finding} />
        ))}
      </div>
    </div>
  );
}
