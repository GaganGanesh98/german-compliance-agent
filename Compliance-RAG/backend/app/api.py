from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent.graph import run_agent

app = FastAPI(title="Compliance RAG Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    regulation: str | None = None


class Citation(BaseModel):
    regulation_code: str
    article_ref: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    documents: list[dict]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    result = run_agent(request.question, regulation=request.regulation)
    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        documents=result["documents"],
    )
