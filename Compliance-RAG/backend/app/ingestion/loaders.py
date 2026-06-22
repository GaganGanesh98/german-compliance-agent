from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class LoadedDocument:
    title: str
    raw_text: str
    regulation_code: str | None


REGULATION_CODE_MAP: dict[str, str] = {
    "gdpr": "GDPR",
    "eu_ai_act": "EU_AI_ACT",
    "ai_act": "EU_AI_ACT",
    "kschg": "KSchG",
    "arbzg": "ArbZG",
    "burlg": "BUrlG",
    "tzbfg": "TzBfG",
}


def infer_regulation_code(filename: str) -> str | None:
    stem = Path(filename).stem.lower().replace("-", "_").replace(" ", "_")
    return REGULATION_CODE_MAP.get(stem)


def load_txt(path: Path) -> LoadedDocument:
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    title = path.stem
    return LoadedDocument(
        title=title,
        raw_text=raw_text,
        regulation_code=infer_regulation_code(path.name),
    )


def load_pdf(path: Path) -> LoadedDocument:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    raw_text = "\n".join(pages)
    title = path.stem
    return LoadedDocument(
        title=title,
        raw_text=raw_text,
        regulation_code=infer_regulation_code(path.name),
    )


def load_document(path: Path) -> LoadedDocument:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".pdf":
        return load_pdf(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")
