"use client";

import { useRouter } from "next/navigation";

import {
  buildFindingContext,
  writePendingFollowUp,
  type AuditFinding,
} from "@/lib/api";

import { SeverityBadge } from "@/components/SeverityBadge";
import { StatusBadge } from "@/components/StatusBadge";

interface FindingCardProps {
  finding: AuditFinding;
}

export function FindingCard({ finding }: FindingCardProps) {
  const router = useRouter();

  function handleAskFollowUp() {
    writePendingFollowUp({
      question: `Regarding ${finding.regulation_code} ${finding.article_ref}: what would make this clause compliant?`,
      regulation: finding.regulation_code,
      findingContext: buildFindingContext(finding),
    });
    // Same-tab navigation only — sessionStorage is per-tab, so a new tab would
    // silently lose the context.
    router.push("/ask");
  }

  return (
    <article className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <StatusBadge status={finding.status} />
        <SeverityBadge severity={finding.severity} />
        <span className="text-sm font-medium text-zinc-800">
          {finding.regulation_code} {finding.article_ref}
        </span>
      </div>

      <p className="mb-2 text-sm font-medium text-zinc-700">{finding.obligation}</p>
      <p className="mb-4 text-sm leading-relaxed text-zinc-600">{finding.rationale}</p>

      {finding.contract_excerpt ? (
        <blockquote className="border-l-4 border-zinc-300 bg-zinc-50 px-4 py-3 text-sm italic leading-relaxed text-zinc-700">
          {finding.contract_excerpt}
        </blockquote>
      ) : (
        <p className="text-sm text-zinc-400">Not addressed in document</p>
      )}

      <div className="mt-4">
        <button
          type="button"
          onClick={handleAskFollowUp}
          className="text-sm font-medium text-zinc-700 underline-offset-4 transition-colors hover:text-zinc-900 hover:underline"
        >
          Ask a follow-up →
        </button>
      </div>
    </article>
  );
}
