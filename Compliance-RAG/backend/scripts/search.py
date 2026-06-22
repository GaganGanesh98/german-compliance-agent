import argparse

from app.embeddings import get_embedder
from app.retrieval import similarity_search


def main() -> None:
    parser = argparse.ArgumentParser(description="Search ingested regulation chunks.")
    parser.add_argument("query", type=str, help="Natural-language search query.")
    parser.add_argument("-k", type=int, default=5, help="Number of results to return.")
    parser.add_argument(
        "--regulation",
        type=str,
        default=None,
        help="Optional regulation code filter (e.g. GDPR).",
    )
    args = parser.parse_args()

    embedder = get_embedder()
    results = similarity_search(
        args.query,
        embedder,
        k=args.k,
        regulation=args.regulation,
    )

    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):
        article = result.article_ref or "N/A"
        regulation = result.regulation_code or "N/A"
        print(f"\n[{index}] similarity={result.similarity:.4f} | {regulation} | {article}")
        print(result.content[:500])
        if len(result.content) > 500:
            print("...")


if __name__ == "__main__":
    main()
