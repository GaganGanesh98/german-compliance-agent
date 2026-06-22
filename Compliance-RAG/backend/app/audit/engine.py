from datetime import UTC, datetime

from app.audit.checkpoints import Checkpoint, get_checkpoints
from app.audit.schema import (
    AuditFinding,
    AuditFindingAssessment,
    AuditReport,
    Severity,
    Status,
)
from app.embeddings import Embedder, get_embedder
from app.llm import get_llm
from app.retrieval import SearchResult, similarity_search

AUDIT_PROMPT = """You are a GDPR compliance auditor reviewing an employment-related document.

Assess whether the document addresses the regulatory obligation below.

Obligation:
{obligation}

Regulation article excerpts ({regulation_code} {article_ref}):
{regulation_text}

Candidate contract clauses from the uploaded document:
{contract_clauses}

Rules:
- If no contract clause meaningfully addresses the obligation, set status to NOT_ADDRESSED and contract_excerpt to null.
- contract_excerpt must be a verbatim quote copied exactly from the candidate contract clauses, or null.
- Do not invent or paraphrase contract text in contract_excerpt.
- rationale must reference both the contract (if any) and the regulation article.
- Choose severity by real-world risk (e.g. missing lawful basis or retention = HIGH; minor wording gaps = LOW).
- status must be one of: COMPLIANT, PARTIAL, VIOLATION, NOT_ADDRESSED.
"""

STATUS_SORT_WEIGHT = {
    Status.VIOLATION: 0,
    Status.PARTIAL: 1,
    Status.NOT_ADDRESSED: 2,
    Status.COMPLIANT: 3,
}

SEVERITY_SORT_WEIGHT = {
    Severity.HIGH: 0,
    Severity.MEDIUM: 1,
    Severity.LOW: 2,
    Severity.INFO: 3,
}


def _format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return "(none found)"
    parts: list[str] = []
    for index, result in enumerate(results):
        article = result.article_ref or "N/A"
        regulation = result.regulation_code or "N/A"
        parts.append(f"[{index}] ({regulation} {article})\n{result.content}")
    return "\n\n".join(parts)


def _build_finding(
    checkpoint: Checkpoint,
    assessment: AuditFindingAssessment,
) -> AuditFinding:
    excerpt = assessment.contract_excerpt
    if assessment.status == Status.NOT_ADDRESSED:
        excerpt = None

    return AuditFinding(
        checkpoint_id=checkpoint.id,
        regulation_code=checkpoint.regulation_code,
        article_ref=checkpoint.article_ref,
        obligation=checkpoint.obligation,
        status=assessment.status,
        severity=assessment.severity,
        rationale=assessment.rationale,
        contract_excerpt=excerpt,
    )


def _assess_checkpoint(
    checkpoint: Checkpoint,
    *,
    document_id: str,
    embedder: Embedder,
) -> AuditFinding:
    contract_hits = similarity_search(
        checkpoint.query,
        embedder,
        k=4,
        document_id=document_id,
    )
    regulation_hits = similarity_search(
        checkpoint.obligation,
        embedder,
        k=2,
        regulation=checkpoint.regulation_code,
    )

    prompt = AUDIT_PROMPT.format(
        obligation=checkpoint.obligation,
        regulation_code=checkpoint.regulation_code,
        article_ref=checkpoint.article_ref,
        regulation_text=_format_search_results(regulation_hits),
        contract_clauses=_format_search_results(contract_hits),
    )

    llm = get_llm()
    structured_llm = llm.with_structured_output(AuditFindingAssessment)
    assessment = structured_llm.invoke(prompt)
    return _build_finding(checkpoint, assessment)


def sort_findings(findings: list[AuditFinding]) -> list[AuditFinding]:
    return sorted(
        findings,
        key=lambda finding: (
            STATUS_SORT_WEIGHT[finding.status],
            SEVERITY_SORT_WEIGHT[finding.severity],
            finding.checkpoint_id,
        ),
    )


def summarize_findings(findings: list[AuditFinding]) -> dict[str, int]:
    summary = {status.value: 0 for status in Status}
    for finding in findings:
        summary[finding.status.value] += 1
    return summary


def run_audit(document_id: str, document_title: str) -> AuditReport:
    embedder = get_embedder()
    findings = [
        _assess_checkpoint(checkpoint, document_id=document_id, embedder=embedder)
        for checkpoint in get_checkpoints()
    ]
    sorted_findings = sort_findings(findings)
    return AuditReport(
        document_title=document_title,
        generated_at=datetime.now(UTC).isoformat(),
        summary=summarize_findings(sorted_findings),
        findings=sorted_findings,
    )
