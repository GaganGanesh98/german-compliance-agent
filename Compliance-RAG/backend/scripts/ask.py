import argparse
import json

from app.agent.graph import run_agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the compliance RAG agent.")
    parser.add_argument("question", type=str, help="Question to ask.")
    parser.add_argument(
        "--regulation",
        type=str,
        default=None,
        help="Optional regulation code filter (e.g. GDPR).",
    )
    args = parser.parse_args()

    result = run_agent(args.question, regulation=args.regulation)

    print("=== Answer ===")
    print(result["answer"])
    print()

    print("=== Citations ===")
    if result["citations"]:
        for citation in result["citations"]:
            print(f"- {citation['regulation_code']} {citation['article_ref']}")
    else:
        print("(none)")
    print()

    print("=== Trace ===")
    trace = result.get("trace", [])
    print(" → ".join(trace) if trace else "(empty)")
    print(
        f"retrieval rewrites: {result.get('retrieval_tries', 0)}, "
        f"generation retries: {result.get('generation_tries', 0)}"
    )
    print()

    print("=== Documents used ===")
    print(json.dumps(result.get("documents", []), indent=2))


if __name__ == "__main__":
    main()
