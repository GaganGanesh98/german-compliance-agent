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

Status definitions (choose the single best fit — do NOT default to PARTIAL when unsure):
- COMPLIANT: a clause clearly and adequately satisfies the obligation. Minor wording imperfections do not downgrade this.
- PARTIAL: a clause addresses the obligation but has a real, specific gap or ambiguity. You must name the gap in the rationale.
- VIOLATION: a clause addresses the topic but in a way that contradicts or breaches the regulation (e.g. consent that is not freely given, an unlawful basis).
- NOT_ADDRESSED: no clause meaningfully addresses the obligation at all.

Rules:
- Decide COMPLIANT vs PARTIAL on substance: if the clause genuinely covers what the article requires, choose COMPLIANT. Only choose PARTIAL if you can state the concrete missing element.
- If status is NOT_ADDRESSED, set contract_excerpt to null.
- contract_excerpt must be a verbatim quote copied exactly from the candidate contract clauses above, or null. Do not invent or paraphrase.
- rationale must reference both the contract (if any) and the regulation article, and for PARTIAL/VIOLATION must state the specific gap or conflict.
- Choose severity by real-world risk (e.g. missing lawful basis or retention = HIGH; minor wording gaps = LOW; an addressed-and-compliant obligation = INFO).
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


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _validate_excerpt(excerpt: str | None, contract_hits: list[SearchResult]) -> str | None:
    """Keep contract_excerpt only if it is genuinely present (verbatim, modulo
    whitespace) in the retrieved clauses. Guards against a hallucinated quote."""
    if not excerpt:
        return None
    needle = _normalize(excerpt)
    if len(needle) < 8:
        return None
    for hit in contract_hits:
        if needle in _normalize(hit.content):
            return excerpt
    return None


def _build_finding(
    checkpoint: Checkpoint,
    assessment: AuditFindingAssessment,
    contract_hits: list[SearchResult],
) -> AuditFinding:
    excerpt = assessment.contract_excerpt
    if assessment.status == Status.NOT_ADDRESSED:
        excerpt = None
    else:
        excerpt = _validate_excerpt(excerpt, contract_hits)

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
    return _build_finding(checkpoint, assessment, contract_hits)


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
