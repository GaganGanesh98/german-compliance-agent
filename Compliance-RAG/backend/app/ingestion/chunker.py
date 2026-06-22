import re
from dataclasses import dataclass

import tiktoken

ARTICLE_BOUNDARY_PATTERN = re.compile(
    r"(?m)^[ \t]*(?:Article\s+\d+|Art\.\s*\d+|§\s*\d+)\b",
    re.IGNORECASE,
)
ARTICLE_REF_PATTERN = re.compile(
    r"^(?:Article\s+(\d+)|Art\.\s*(\d+)|§\s*(\d+))",
    re.IGNORECASE,
)

DEFAULT_ENCODING = "cl100k_base"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 80


@dataclass(frozen=True)
class TextChunk:
    content: str
    article_ref: str | None
    chunk_index: int
    token_count: int


def _get_encoder() -> tiktoken.Encoding:
    return tiktoken.get_encoding(DEFAULT_ENCODING)


def _extract_article_ref(text: str) -> str | None:
    match = ARTICLE_REF_PATTERN.search(text.strip())
    if not match:
        return None
    if match.group(1):
        return f"Art. {match.group(1)}"
    if match.group(2):
        return f"Art. {match.group(2)}"
    if match.group(3):
        return f"§ {match.group(3)}"
    return None


def _split_by_tokens(
    text: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
    encoder: tiktoken.Encoding,
) -> list[str]:
    tokens = encoder.encode(text)
    if not tokens:
        return []
    if len(tokens) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(encoder.decode(chunk_tokens))
        if end >= len(tokens):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    encoder = _get_encoder()
    normalized = text.strip()
    if not normalized:
        return []

    boundaries = list(ARTICLE_BOUNDARY_PATTERN.finditer(normalized))
    if not boundaries:
        sub_chunks = _split_by_tokens(
            normalized,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            encoder=encoder,
        )
        return [
            TextChunk(
                content=content,
                article_ref=None,
                chunk_index=index,
                token_count=len(encoder.encode(content)),
            )
            for index, content in enumerate(sub_chunks)
        ]

    article_sections: list[tuple[str | None, str]] = []

    # Retain any preamble/recitals before the first article boundary as an
    # unattributed section (article_ref=None) rather than dropping it.
    first_start = boundaries[0].start()
    if first_start > 0:
        preamble = normalized[:first_start].strip()
        if preamble:
            article_sections.append((None, preamble))

    for index, match in enumerate(boundaries):
        start = match.start()
        end = boundaries[index + 1].start() if index + 1 < len(boundaries) else len(normalized)
        section = normalized[start:end].strip()
        if section:
            article_sections.append((_extract_article_ref(section), section))

    chunks: list[TextChunk] = []
    chunk_index = 0
    for article_ref, section in article_sections:
        sub_chunks = _split_by_tokens(
            section,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            encoder=encoder,
        )
        for content in sub_chunks:
            chunks.append(
                TextChunk(
                    content=content,
                    article_ref=article_ref,
                    chunk_index=chunk_index,
                    token_count=len(encoder.encode(content)),
                )
            )
            chunk_index += 1

    return chunks
