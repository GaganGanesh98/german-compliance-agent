from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import Any
from uuid import UUID

import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.config import settings


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        register_vector(conn)
        yield conn


def upsert_document(
    conn: psycopg.Connection,
    *,
    title: str,
    source_type: str,
    regulation_code: str | None,
) -> UUID:
    row = conn.execute(
        """
        insert into documents (title, source_type, regulation_code)
        values (%s, %s, %s)
        on conflict (title) do update
            set source_type = excluded.source_type,
                regulation_code = excluded.regulation_code
        returning id
        """,
        (title, source_type, regulation_code),
    ).fetchone()
    assert row is not None
    return row["id"]


def delete_chunks_for_document(conn: psycopg.Connection, document_id: UUID) -> None:
    conn.execute("delete from chunks where document_id = %s", (document_id,))


def bulk_insert_chunks(
    conn: psycopg.Connection,
    *,
    document_id: UUID,
    chunks: Sequence[dict[str, Any]],
) -> int:
    if not chunks:
        return 0

    rows = [
        (
            document_id,
            chunk["content"],
            chunk["chunk_index"],
            chunk.get("article_ref"),
            chunk["token_count"],
            chunk["embedding"],
        )
        for chunk in chunks
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            insert into chunks (
                document_id, content, chunk_index, article_ref, token_count, embedding
            )
            values (%s, %s, %s, %s, %s, %s)
            """,
            rows,
        )
    return len(rows)


def match_chunks(
    conn: psycopg.Connection,
    *,
    query_embedding: list[float],
    match_count: int,
    filter_regulation: str | None = None,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select content, article_ref, regulation_code, similarity
        from match_chunks(%s::vector, %s, %s)
        """,
        (query_embedding, match_count, filter_regulation),
    ).fetchall()
    return list(rows)
