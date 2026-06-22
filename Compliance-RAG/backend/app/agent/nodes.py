import json
import re
from typing import Any

from langgraph.graph import END

from app.agent.prompts import (
    GENERATE_PROMPT,
    GRADE_DOCUMENTS_BATCH_PROMPT,
    GRADE_GENERATION_PROMPT,
    REWRITE_QUERY_PROMPT,
)
from app.agent.state import GraphState
from app.embeddings import get_embedder
from app.llm import get_llm
from app.retrieval import similarity_search


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


def _format_citation(doc: dict) -> str:
    regulation = doc.get("regulation_code") or "UNKNOWN"
    article = doc.get("article_ref") or "N/A"
    return f"[{regulation} {article}]"


def _format_documents(documents: list[dict]) -> str:
    if not documents:
        return "(no documents)"

    parts: list[str] = []
    for index, doc in enumerate(documents):
        citation = _format_citation(doc)
        parts.append(f"[{index}] {citation}\n{doc.get('content', '')}")
    return "\n\n".join(parts)


def retrieve(state: GraphState) -> dict:
    results = similarity_search(
        state["question"],
        get_embedder(),
        k=6,
        regulation=state.get("regulation"),
    )
    documents = [result.model_dump() for result in results]
    return {"documents": documents}


def grade_documents(state: GraphState) -> dict:
    documents = state.get("documents", [])
    if not documents:
        return {"documents": []}

    llm = get_llm()
    chunks_text = "\n\n".join(
        f"{index}. {_format_citation(doc)}\n{doc.get('content', '')}"
        for index, doc in enumerate(documents)
    )
    prompt = GRADE_DOCUMENTS_BATCH_PROMPT.format(
        question=state["original_question"],
        chunks=chunks_text,
    )
    response = llm.invoke(prompt)
    grades = _parse_json_object(str(response.content))

    relevant_documents: list[dict] = []
    for index, doc in enumerate(documents):
        verdict = str(grades.get(str(index), grades.get(index, "no"))).lower()
        if verdict == "yes":
            relevant_documents.append(doc)

    return {"documents": relevant_documents}


def transform_query(state: GraphState) -> dict:
    llm = get_llm()
    prompt = REWRITE_QUERY_PROMPT.format(
        original_question=state["original_question"],
        question=state["question"],
    )
    response = llm.invoke(prompt)
    rewritten = str(response.content).strip()
    return {
        "question": rewritten,
        "retrieval_tries": state.get("retrieval_tries", 0) + 1,
    }


def generate(state: GraphState) -> dict:
    llm = get_llm()
    context = _format_documents(state.get("documents", []))
    prompt = GENERATE_PROMPT.format(
        question=state["original_question"],
        context=context,
    )
    response = llm.invoke(prompt)
    return {
        "generation": str(response.content).strip(),
        "generation_tries": state.get("generation_tries", 0) + 1,
    }


def decide_to_generate(state: GraphState) -> str:
    if len(state.get("documents", [])) >= 1:
        return "generate"
    if state.get("retrieval_tries", 0) < 2:
        return "transform_query"
    return "generate"


def grade_generation(state: GraphState) -> str:
    llm = get_llm()
    context = _format_documents(state.get("documents", []))
    prompt = GRADE_GENERATION_PROMPT.format(
        question=state["original_question"],
        context=context,
        generation=state.get("generation", ""),
    )
    response = llm.invoke(prompt)
    result = _parse_json_object(str(response.content))

    grounded = str(result.get("grounded", "no")).lower() == "yes"
    addresses = str(result.get("addresses", "no")).lower() == "yes"

    if grounded and addresses:
        return END
    if not grounded and state.get("generation_tries", 0) < 2:
        return "generate"
    if grounded and not addresses and state.get("retrieval_tries", 0) < 2:
        return "transform_query"
    return END
