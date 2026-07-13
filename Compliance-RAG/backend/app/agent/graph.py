from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    decide_to_generate,
    generate,
    grade_documents,
    grade_generation,
    retrieve,
    transform_query,
)
from app.agent.state import GraphState


def dedupe_citations(documents: list[dict]) -> list[dict]:
    seen: set[tuple[str | None, str | None]] = set()
    citations: list[dict] = []

    for doc in documents:
        regulation_code = doc.get("regulation_code")
        article_ref = doc.get("article_ref")
        key = (regulation_code, article_ref)
        if not regulation_code or not article_ref or key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "regulation_code": regulation_code,
                "article_ref": article_ref,
            }
        )

    return citations


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("transform_query", transform_query)
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "generate": "generate",
            "transform_query": "transform_query",
        },
    )
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_conditional_edges(
        "generate",
        grade_generation,
        {
            "generate": "generate",
            "transform_query": "transform_query",
            END: END,
        },
    )

    return workflow.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_agent(
    question: str,
    regulation: str | None = None,
    finding_context: str | None = None,
) -> dict:
    graph = get_graph()
    initial_state: GraphState = {
        "question": question,
        "original_question": question,
        "regulation": regulation,
        "finding_context": finding_context,
        "documents": [],
        "generation": "",
        "retrieval_tries": 0,
        "generation_tries": 0,
    }

    trace: list[str] = []
    final_state = initial_state

    for update in graph.stream(initial_state):
        for node_name, node_state in update.items():
            trace.append(node_name)
            final_state = {**final_state, **node_state}

    documents = final_state.get("documents", [])
    return {
        "answer": final_state.get("generation", ""),
        "citations": dedupe_citations(documents),
        "documents": documents,
        "trace": trace,
        "retrieval_tries": final_state.get("retrieval_tries", 0),
        "generation_tries": final_state.get("generation_tries", 0),
    }
