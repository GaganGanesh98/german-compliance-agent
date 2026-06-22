const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export interface Citation {
  regulation_code: string;
  article_ref: string;
}

export interface RetrievedDocument {
  content: string;
  article_ref: string | null;
  regulation_code: string | null;
  similarity: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  documents: RetrievedDocument[];
  trace: string[];
  retrieval_tries: number;
  generation_tries: number;
}

export type Status = "COMPLIANT" | "PARTIAL" | "VIOLATION" | "NOT_ADDRESSED";
export type Severity = "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface AuditFinding {
  checkpoint_id: string;
  regulation_code: string;
  article_ref: string;
  obligation: string;
  status: Status;
  severity: Severity;
  rationale: string;
  contract_excerpt: string | null;
}

export interface AuditReport {
  document_title: string;
  generated_at: string;
  summary: Record<string, number>;
  findings: AuditFinding[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // fall through
  }
  return `Request failed (${response.status})`;
}

export async function checkHealth(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }
  return response.json() as Promise<{ status: string }>;
}

export async function askQuestion(
  question: string,
  regulation?: string | null,
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, regulation: regulation ?? null }),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  return response.json() as Promise<QueryResponse>;
}

export async function runAudit(file: File): Promise<AuditReport> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/audit`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response), response.status);
  }

  return response.json() as Promise<AuditReport>;
}
