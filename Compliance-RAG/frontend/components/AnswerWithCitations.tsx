import { CitationBadge } from "@/components/CitationBadge";
import type { Citation } from "@/lib/api";

interface AnswerWithCitationsProps {
  answer: string;
  citations: Citation[];
}

function renderAnswerWithCitations(answer: string) {
  const parts = answer.split(/(\[[^\]]+\])/g);

  return parts.map((part, index) => {
    if (part.startsWith("[") && part.endsWith("]")) {
      return (
        <span key={`${part}-${index}`} className="mx-0.5 inline-block align-middle">
          <CitationBadge label={part.slice(1, -1)} />
        </span>
      );
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

export function AnswerWithCitations({ answer, citations }: AnswerWithCitationsProps) {
  return (
    <div className="space-y-4">
      <div className="text-base leading-7 text-zinc-800">
        {renderAnswerWithCitations(answer)}
      </div>
      {citations.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {citations.map((citation) => (
            <CitationBadge
              key={`${citation.regulation_code}-${citation.article_ref}`}
              label={`${citation.regulation_code} ${citation.article_ref}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
