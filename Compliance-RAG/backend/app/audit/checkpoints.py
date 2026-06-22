from dataclasses import dataclass


@dataclass(frozen=True)
class Checkpoint:
    id: str
    regulation_code: str
    article_ref: str
    title: str
    obligation: str
    query: str


GDPR_EMPLOYMENT_CHECKPOINTS: list[Checkpoint] = [
    Checkpoint(
        id="gdpr-art6-lawful-basis",
        regulation_code="GDPR",
        article_ref="Art. 6",
        title="Lawful basis for processing employee data",
        obligation=(
            "Processing of personal data must have a lawful basis, such as consent, "
            "contract performance, legal obligation, vital interests, public interest, "
            "or legitimate interests."
        ),
        query=(
            "lawful basis legal ground for processing employee personal data "
            "consent contract legitimate interest"
        ),
    ),
    Checkpoint(
        id="gdpr-art7-consent",
        regulation_code="GDPR",
        article_ref="Art. 7",
        title="Consent conditions and freely-given consent in employment",
        obligation=(
            "Where processing is based on consent, the controller must be able to "
            "demonstrate consent was given. Consent must be freely given, specific, "
            "informed, and unambiguous; withdrawal must be as easy as giving consent."
        ),
        query=(
            "employee consent personal data processing freely given withdraw consent "
            "demonstrate consent employment"
        ),
    ),
    Checkpoint(
        id="gdpr-art9-special-categories",
        regulation_code="GDPR",
        article_ref="Art. 9",
        title="Special-category data such as health information",
        obligation=(
            "Processing of special categories of personal data, including health data, "
            "is prohibited unless a specific legal basis applies, such as explicit consent "
            "or employment law authorization."
        ),
        query=(
            "health data medical information special category sensitive personal data "
            "employee health records"
        ),
    ),
    Checkpoint(
        id="gdpr-art13-transparency",
        regulation_code="GDPR",
        article_ref="Art. 13",
        title="Transparency and information to data subjects",
        obligation=(
            "When personal data are collected from the data subject, the controller "
            "must provide identity and contact details, processing purposes, legal basis, "
            "recipients, retention period, and data subject rights."
        ),
        query=(
            "privacy notice information to employee data subject processing purposes "
            "legal basis retention rights contact details"
        ),
    ),
    Checkpoint(
        id="gdpr-art5-purpose-minimisation",
        regulation_code="GDPR",
        article_ref="Art. 5",
        title="Purpose limitation and data minimisation",
        obligation=(
            "Personal data must be collected for specified, explicit, and legitimate "
            "purposes and limited to what is adequate, relevant, and necessary."
        ),
        query=(
            "purpose limitation data minimisation adequate relevant necessary "
            "specified purposes employee data"
        ),
    ),
    Checkpoint(
        id="gdpr-art5-storage-limitation",
        regulation_code="GDPR",
        article_ref="Art. 5(1)(e)",
        title="Storage limitation and retention period",
        obligation=(
            "Personal data must be kept in a form permitting identification for no "
            "longer than necessary for the purposes for which they are processed."
        ),
        query=(
            "data retention storage period delete personal data retention policy "
            "how long employee data kept"
        ),
    ),
    Checkpoint(
        id="gdpr-art15-17-data-subject-rights",
        regulation_code="GDPR",
        article_ref="Art. 15–17",
        title="Data subject rights including access and erasure",
        obligation=(
            "Data subjects have the right to access their personal data, request "
            "rectification, and request erasure where applicable."
        ),
        query=(
            "data subject rights access erasure deletion rectification employee "
            "request personal data copy"
        ),
    ),
    Checkpoint(
        id="gdpr-art32-security",
        regulation_code="GDPR",
        article_ref="Art. 32",
        title="Security of processing",
        obligation=(
            "The controller must implement appropriate technical and organisational "
            "measures to ensure a level of security appropriate to the risk."
        ),
        query=(
            "security measures technical organisational safeguards protect personal data "
            "confidentiality integrity employee data"
        ),
    ),
    Checkpoint(
        id="gdpr-art44-46-transfers",
        regulation_code="GDPR",
        article_ref="Art. 44–46",
        title="International transfers of personal data",
        obligation=(
            "Transfers of personal data to third countries require an adequacy decision, "
            "appropriate safeguards, or a specific derogation."
        ),
        query=(
            "international transfer third country cross-border data transfer "
            "adequacy safeguards employee data abroad"
        ),
    ),
    Checkpoint(
        id="gdpr-art88-employment",
        regulation_code="GDPR",
        article_ref="Art. 88",
        title="Processing in the employment context",
        obligation=(
            "Member States may provide for more specific rules on processing employee "
            "personal data in the employment context, including for recruitment, "
            "performance of the employment contract, and health and safety."
        ),
        query=(
            "employment context employee monitoring workplace processing recruitment "
            "performance contract health safety"
        ),
    ),
]


def get_checkpoints(regulation_code: str | None = None) -> list[Checkpoint]:
    if regulation_code is None:
        return list(GDPR_EMPLOYMENT_CHECKPOINTS)
    return [
        checkpoint
        for checkpoint in GDPR_EMPLOYMENT_CHECKPOINTS
        if checkpoint.regulation_code == regulation_code
    ]
