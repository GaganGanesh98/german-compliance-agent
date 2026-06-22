interface CitationBadgeProps {
  label: string;
}

export function CitationBadge({ label }: CitationBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-200">
      {label}
    </span>
  );
}
