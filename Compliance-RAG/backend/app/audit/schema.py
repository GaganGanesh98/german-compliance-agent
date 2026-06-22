from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    VIOLATION = "VIOLATION"
    NOT_ADDRESSED = "NOT_ADDRESSED"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AuditFinding(BaseModel):
    checkpoint_id: str
    regulation_code: str
    article_ref: str
    obligation: str
    status: Status
    severity: Severity
    rationale: str
    contract_excerpt: str | None = None


class AuditFindingAssessment(BaseModel):
    """LLM-produced fields only; checkpoint metadata is merged in by the engine."""

    status: Status
    severity: Severity
    rationale: str = Field(
        description="Explain the finding, referencing both the contract clause and regulation article."
    )
    contract_excerpt: str | None = Field(
        default=None,
        description="Verbatim quote from the provided contract clauses, or null if NOT_ADDRESSED.",
    )


class AuditReport(BaseModel):
    document_title: str
    generated_at: str
    summary: dict[str, int]
    findings: list[AuditFinding]
