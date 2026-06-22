import os

import pytest

from app.agent.graph import build_graph, dedupe_citations, get_graph, run_agent


def test_graph_compiles() -> None:
    graph = build_graph()
    assert graph is not None


def test_run_agent_importable() -> None:
    assert callable(run_agent)


def test_get_graph_is_singleton() -> None:
    assert get_graph() is get_graph()


def test_dedupe_citations() -> None:
    documents = [
        {"regulation_code": "GDPR", "article_ref": "Art. 6", "content": "a"},
        {"regulation_code": "GDPR", "article_ref": "Art. 6", "content": "b"},
        {"regulation_code": "GDPR", "article_ref": "Art. 7", "content": "c"},
        {"regulation_code": None, "article_ref": "Art. 1", "content": "d"},
        {"regulation_code": "BDSG", "article_ref": None, "content": "e"},
    ]

    citations = dedupe_citations(documents)

    assert citations == [
        {"regulation_code": "GDPR", "article_ref": "Art. 6"},
        {"regulation_code": "GDPR", "article_ref": "Art. 7"},
    ]


@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"),
    reason="GROQ_API_KEY not set",
)
def test_run_agent_gdpr_question() -> None:
    result = run_agent(
        "What is the lawful basis for processing personal data?",
        regulation="GDPR",
    )

    assert result["answer"]
    assert "trace" in result
    assert "retrieve" in result["trace"]
    assert "grade_documents" in result["trace"]
    assert "generate" in result["trace"]
