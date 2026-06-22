from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.db import bulk_insert_chunks, delete_chunks_for_document, get_connection, upsert_document
from app.embeddings import Embedder
from app.ingestion.chunker import TextChunk, chunk_text
from app.ingestion.loaders import load_document


@dataclass(frozen=True)
class IngestionResult:
    title: str
    chunk_count: int
    token_count: int
    document_id: UUID


@dataclass(frozen=True)
class IngestionSummary:
    documents: int
    chunks: int
    tokens: int
    results: list[IngestionResult]


def ingest_file(
    path: Path,
    embedder: Embedder,
    *,
    source_type: str = "regulation",
) -> IngestionResult:
    loaded = load_document(path)
    chunks = chunk_text(loaded.raw_text)

    with get_connection() as conn:
        document_id = upsert_document(
            conn,
            title=loaded.title,
            source_type=source_type,
            regulation_code=loaded.regulation_code if source_type == "regulation" else None,
        )
        delete_chunks_for_document(conn, document_id)

        if chunks:
            embeddings = embedder.embed_documents([chunk.content for chunk in chunks])
            chunk_rows = _build_chunk_rows(chunks, embeddings)
            bulk_insert_chunks(conn, document_id=document_id, chunks=chunk_rows)

        conn.commit()

    token_count = sum(chunk.token_count for chunk in chunks)
    return IngestionResult(
        title=loaded.title,
        chunk_count=len(chunks),
        token_count=token_count,
        document_id=document_id,
    )


def ingest_user_document(path: Path, embedder: Embedder) -> UUID:
    result = ingest_file(path, embedder, source_type="user_upload")
    return result.document_id


def ingest_directory(source_dir: Path, embedder: Embedder) -> IngestionSummary:
    paths = sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".pdf", ".txt"}
    )

    results: list[IngestionResult] = []
    for path in paths:
        results.append(ingest_file(path, embedder))

    return IngestionSummary(
        documents=len(results),
        chunks=sum(result.chunk_count for result in results),
        tokens=sum(result.token_count for result in results),
        results=results,
    )


def _build_chunk_rows(
    chunks: list[TextChunk],
    embeddings: list[list[float]],
) -> list[dict[str, object]]:
    return [
        {
            "content": chunk.content,
            "chunk_index": chunk.chunk_index,
            "article_ref": chunk.article_ref,
            "token_count": chunk.token_count,
            "embedding": embedding,
        }
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]
