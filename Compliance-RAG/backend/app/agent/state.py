from typing import TypedDict


class GraphState(TypedDict):
    question: str
    original_question: str
    regulation: str | None
    finding_context: str | None
    documents: list[dict]
    generation: str
    retrieval_tries: int
    generation_tries: int
