import type { Status } from "@/lib/api";

const STATUS_STYLES: Record<Status, string> = {
  VIOLATION: "bg-red-50 text-red-700 ring-red-200",
  PARTIAL: "bg-amber-50 text-amber-800 ring-amber-200",
  NOT_ADDRESSED: "bg-orange-50 text-orange-800 ring-orange-200",
  COMPLIANT: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

interface StatusBadgeProps {
  status: Status;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {status.replace("_", " ")}
    </span>
  );
}
