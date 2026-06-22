from pydantic import BaseModel

from app.db import get_connection, match_chunks as db_match_chunks
from app.embeddings import Embedder


class SearchResult(BaseModel):
    content: str
    article_ref: str | None
    regulation_code: str | None
    similarity: float


def similarity_search(
    query: str,
    embedder: Embedder,
    *,
    k: int = 5,
    regulation: str | None = None,
    document_id: str | None = None,
) -> list[SearchResult]:
    query_embedding = embedder.embed_query(query)
    with get_connection() as conn:
        rows = db_match_chunks(
            conn,
            query_embedding=query_embedding,
            match_count=k,
            filter_regulation=regulation,
            filter_document_id=document_id,
        )

    return [
        SearchResult(
            content=row["content"],
            article_ref=row["article_ref"],
            regulation_code=row["regulation_code"],
            similarity=float(row["similarity"]),
        )
        for row in rows
    ]
