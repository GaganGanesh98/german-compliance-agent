from pathlib import Path
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent.graph import run_agent
from app.audit.engine import run_audit
from app.audit.schema import AuditReport
from app.embeddings import get_embedder
from app.ingestion.pipeline import ingest_user_document

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
    trace: list[str] = []
    retrieval_tries: int = 0
    generation_tries: int = 0


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
        trace=result.get("trace", []),
        retrieval_tries=result.get("retrieval_tries", 0),
        generation_tries=result.get("generation_tries", 0),
    )


@app.post("/audit", response_model=AuditReport)
async def audit(file: UploadFile = File(...)) -> AuditReport:
    suffix = Path(file.filename or "upload.txt").suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        raise HTTPException(status_code=400, detail="Only .pdf and .txt uploads are supported.")

    contents = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    embedder = get_embedder()
    document_id = ingest_user_document(tmp_path, embedder)
    document_title = Path(file.filename or tmp_path.stem).stem
    return run_audit(str(document_id), document_title)
