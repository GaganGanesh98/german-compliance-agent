import os
from unittest.mock import MagicMock

import pytest

from app.agent import nodes
from app.agent.graph import build_graph, dedupe_citations, get_graph, run_agent
from app.agent.nodes import generate
from app.agent.prompts import GENERATE_PROMPT


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


def _make_state(**overrides: object) -> dict:
    state = {
        "question": "What makes this clause compliant?",
        "original_question": "What makes this clause compliant?",
        "regulation": "GDPR",
        "finding_context": None,
        "documents": [{"regulation_code": "GDPR", "article_ref": "Art. 6", "content": "excerpt"}],
        "generation": "",
        "retrieval_tries": 0,
        "generation_tries": 0,
    }
    state.update(overrides)
    return state


def _capture_generate_prompt(monkeypatch: pytest.MonkeyPatch, state: dict) -> str:
    """Run the generate node with a mocked LLM and return the prompt it received."""
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="answer")
    monkeypatch.setattr(nodes, "get_llm", lambda: llm)

    generate(state)

    llm.invoke.assert_called_once()
    return llm.invoke.call_args.args[0]


def test_generate_injects_finding_context(monkeypatch: pytest.MonkeyPatch) -> None:
    finding = "GDPR Art. 6 | PARTIAL | excerpt: 'we process data' | rationale: no lawful basis stated"
    state = _make_state(finding_context=finding)

    prompt = _capture_generate_prompt(monkeypatch, state)

    # The finding is fenced and framed as untrusted data, not instructions.
    assert "BEGIN AUDIT FINDING" in prompt
    assert "END AUDIT FINDING" in prompt
    assert "untrusted" in prompt
    assert finding in prompt


def test_generate_omits_finding_context_when_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _make_state(finding_context=None)

    prompt = _capture_generate_prompt(monkeypatch, state)

    assert "BEGIN AUDIT FINDING" not in prompt
    # Prompt body is byte-identical to the no-context prompt.
    assert prompt == GENERATE_PROMPT.format(
        finding_context="",
        question=state["original_question"],
        context="[0] [GDPR Art. 6]\nexcerpt",
    )


def test_run_agent_seeds_finding_context(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    class FakeGraph:
        def stream(self, initial_state: dict):
            captured.update(initial_state)
            yield {"generate": {"generation": "grounded answer"}}

    monkeypatch.setattr("app.agent.graph.get_graph", lambda: FakeGraph())

    finding = "GDPR Art. 9 | VIOLATION | health data without explicit consent"
    result = run_agent("Explain this", regulation="GDPR", finding_context=finding)

    assert captured["finding_context"] == finding
    assert captured["regulation"] == "GDPR"
    assert result["answer"] == "grounded answer"


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
