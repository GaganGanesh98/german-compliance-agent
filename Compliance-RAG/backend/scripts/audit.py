import argparse
from pathlib import Path

from app.audit.engine import run_audit
from app.audit.schema import Severity, Status
from app.embeddings import get_embedder
from app.ingestion.pipeline import ingest_user_document

SEVERITY_ORDER = [Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
STATUS_LABELS = {
    Status.COMPLIANT: "COMPLIANT",
    Status.PARTIAL: "PARTIAL",
    Status.VIOLATION: "VIOLATION",
    Status.NOT_ADDRESSED: "NOT_ADDRESSED",
}


def _print_summary(summary: dict[str, int]) -> None:
    parts = [f"{status}={count}" for status, count in summary.items() if count]
    print("Summary:", ", ".join(parts) if parts else "(no findings)")


def _print_findings(report) -> None:
    findings_by_severity: dict[Severity, list] = {level: [] for level in SEVERITY_ORDER}
    for finding in report.findings:
        findings_by_severity[finding.severity].append(finding)

    for severity in SEVERITY_ORDER:
        group = findings_by_severity[severity]
        if not group:
            continue

        print(f"\n{'=' * 72}")
        print(f"{severity.value} ({len(group)})")
        print("=" * 72)

        for finding in group:
            print(f"\n[{finding.status.value}] {finding.regulation_code} {finding.article_ref}")
            print(f"Checkpoint: {finding.checkpoint_id}")
            print(f"Obligation: {finding.obligation}")
            print(f"Rationale: {finding.rationale}")
            if finding.contract_excerpt:
                print(f"Contract excerpt: {finding.contract_excerpt}")
            else:
                print("Contract excerpt: (none)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a GDPR compliance audit on a document.")
    parser.add_argument("path", type=Path, help="Path to a PDF or TXT document.")
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"File not found: {args.path}")
    if args.path.suffix.lower() not in {".pdf", ".txt"}:
        raise SystemExit("Only .pdf and .txt files are supported.")

    embedder = get_embedder()
    print(f"Ingesting {args.path.name} as user document...")
    document_id = ingest_user_document(args.path, embedder)

    print(f"Running audit (document_id={document_id})...")
    report = run_audit(str(document_id), args.path.stem)

    print(f"\nAudit report: {report.document_title}")
    print(f"Generated at: {report.generated_at}")
    _print_summary(report.summary)
    _print_findings(report)


if __name__ == "__main__":
    main()
