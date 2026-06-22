import argparse
from pathlib import Path

from app.embeddings import get_embedder
from app.ingestion.pipeline import ingest_directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest regulation documents into the vector store.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/corpus"),
        help="Directory containing PDF/txt regulation files.",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source directory not found: {args.source}")

    embedder = get_embedder()
    summary = ingest_directory(args.source, embedder)

    print(f"Ingested {summary.documents} document(s), {summary.chunks} chunk(s), {summary.tokens} token(s).")
    for result in summary.results:
        print(f"  - {result.title}: {result.chunk_count} chunks, {result.token_count} tokens")


if __name__ == "__main__":
    main()
