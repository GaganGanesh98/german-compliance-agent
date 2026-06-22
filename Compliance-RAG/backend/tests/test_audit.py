from unittest.mock import MagicMock

import pytest

from app.audit.checkpoints import GDPR_EMPLOYMENT_CHECKPOINTS, get_checkpoints
from app.audit.engine import run_audit, sort_findings, summarize_findings
from app.audit.schema import AuditFinding, AuditFindingAssessment, Severity, Status
from app.retrieval import SearchResult


def _finding(
    *,
    checkpoint_id: str,
    status: Status,
    severity: Severity,
) -> AuditFinding:
    return AuditFinding(
        checkpoint_id=checkpoint_id,
        regulation_code="GDPR",
        article_ref="Art. 6",
        obligation="Test obligation",
        status=status,
        severity=severity,
        rationale="Test rationale",
        contract_excerpt=None,
    )


def test_checkpoints_have_unique_ids() -> None:
    ids = [checkpoint.id for checkpoint in GDPR_EMPLOYMENT_CHECKPOINTS]
    assert len(ids) == len(set(ids))
    assert len(get_checkpoints()) == len(GDPR_EMPLOYMENT_CHECKPOINTS)


def test_sort_findings_violation_high_first() -> None:
    findings = [
        _finding(checkpoint_id="c", status=Status.COMPLIANT, severity=Severity.INFO),
        _finding(checkpoint_id="a", status=Status.VIOLATION, severity=Severity.HIGH),
        _finding(checkpoint_id="b", status=Status.VIOLATION, severity=Severity.MEDIUM),
        _finding(checkpoint_id="d", status=Status.NOT_ADDRESSED, severity=Severity.HIGH),
    ]

    sorted_findings = sort_findings(findings)

    assert sorted_findings[0].status == Status.VIOLATION
    assert sorted_findings[0].severity == Severity.HIGH
    assert sorted_findings[1].status == Status.VIOLATION
    assert sorted_findings[1].severity == Severity.MEDIUM
    assert sorted_findings[2].status == Status.NOT_ADDRESSED
    assert sorted_findings[-1].status == Status.COMPLIANT


def test_summarize_findings_counts_match() -> None:
    findings = [
        _finding(checkpoint_id="a", status=Status.VIOLATION, severity=Severity.HIGH),
        _finding(checkpoint_id="b", status=Status.VIOLATION, severity=Severity.MEDIUM),
        _finding(checkpoint_id="c", status=Status.NOT_ADDRESSED, severity=Severity.HIGH),
        _finding(checkpoint_id="d", status=Status.COMPLIANT, severity=Severity.INFO),
    ]

    summary = summarize_findings(findings)

    assert summary["VIOLATION"] == 2
    assert summary["NOT_ADDRESSED"] == 1
    assert summary["COMPLIANT"] == 1
    assert summary["PARTIAL"] == 0
    assert sum(summary.values()) == len(findings)


def test_run_audit_with_mocked_llm_and_retrieval(monkeypatch: pytest.MonkeyPatch) -> None:
    contract_clause = (
        "The Employer processes employee personal data for payroll and contract performance."
    )
    regulation_clause = "Processing shall be lawful only if at least one lawful basis applies."

    def fake_similarity_search(query, embedder, **kwargs):
        if kwargs.get("document_id"):
            return [
                SearchResult(
                    content=contract_clause,
                    article_ref=None,
                    regulation_code=None,
                    similarity=0.82,
                )
            ]
        return [
            SearchResult(
                content=regulation_clause,
                article_ref="Art. 6",
                regulation_code="GDPR",
                similarity=0.91,
            )
        ]

    assessment = AuditFindingAssessment(
        status=Status.PARTIAL,
        severity=Severity.MEDIUM,
        rationale=(
            "The contract mentions payroll processing but does not specify the lawful basis "
            "required by GDPR Art. 6."
        ),
        contract_excerpt=contract_clause,
    )

    structured_llm = MagicMock()
    structured_llm.invoke.return_value = assessment

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    monkeypatch.setattr("app.audit.engine.similarity_search", fake_similarity_search)
    monkeypatch.setattr("app.audit.engine.get_llm", lambda: llm)
    monkeypatch.setattr(
        "app.audit.engine.get_checkpoints",
        lambda regulation_code=None: [GDPR_EMPLOYMENT_CHECKPOINTS[0]],
    )

    report = run_audit("doc-123", "Sample Contract")

    assert report.document_title == "Sample Contract"
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.checkpoint_id == GDPR_EMPLOYMENT_CHECKPOINTS[0].id
    assert finding.regulation_code == "GDPR"
    assert finding.article_ref == "Art. 6"
    assert finding.obligation == GDPR_EMPLOYMENT_CHECKPOINTS[0].obligation
    assert finding.status == Status.PARTIAL
    assert finding.contract_excerpt == contract_clause
    assert report.summary["PARTIAL"] == 1
