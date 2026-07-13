# German Compliance Audit Agent

A retrieval-augmented compliance assistant for German/EU regulation. It ingests
regulation documents, answers questions grounded in those documents with
citations, and audits uploaded contracts against regulatory obligations.

The project lives under [`Compliance-RAG/`](./Compliance-RAG).

## Features

The system has two connected features:

- **Ask** — a self-corrective RAG agent (LangGraph) that answers compliance
  questions and cites the exact regulation articles it used.
- **Audit** — upload a contract (PDF/TXT) and get a structured report of findings
  (`COMPLIANT` / `PARTIAL` / `VIOLATION` / `NOT_ADDRESSED`) with severity,
  rationale, and the verbatim clause each finding refers to.

The two are bridged: any audit finding has an **"Ask a follow-up"** action that
carries the finding's context into the Ask chat so you can drill into it without
re-typing anything.

## Stack

- **Backend:** Python 3.11+, FastAPI
- **Agent:** LangGraph (self-corrective retrieve → grade → transform → generate loop)
- **LLM:** Groq (`langchain-groq`)
- **Embeddings:** Google Gemini (`gemini-embedding-001`, 1024-dim via MRL; free tier)
- **Vector store:** Supabase Postgres + pgvector (HNSW index, `match_chunks` RPC)
- **Frontend:** Next.js (App Router, React 19)

## Setup

### Backend

1. Create and activate a virtual environment:

```bash
cd Compliance-RAG/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy and fill environment variables:

```bash
cp .env.example .env
```

- `DATABASE_URL` — the **Session pooler** connection string from Supabase → Connect (IPv4-friendly).
- `GOOGLE_API_KEY` — from [Google AI Studio](https://aistudio.google.com/app/apikey) (embeddings).
- `GROQ_API_KEY` — from [Groq](https://console.groq.com/keys) (the agent/audit LLM).

3. Apply the database schema in the Supabase SQL editor by pasting the contents of
   `Compliance-RAG/supabase/schema.sql` (creates the `documents` / `chunks` tables,
   the HNSW index, and the `match_chunks` function).

4. Add regulation files to `Compliance-RAG/backend/data/corpus/` (e.g. `gdpr.txt`, `gdpr.pdf`).

### Frontend

```bash
cd Compliance-RAG/frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL, defaults to http://127.0.0.1:8000
npm run dev
```

## Usage

### CLI (from `Compliance-RAG/backend/`, venv active)

```bash
# Ingest all PDF/txt files in data/corpus/
python -m scripts.ingest --source data/corpus

# Search raw chunks (retrieval only, no agent)
python -m scripts.search "lawful basis for processing personal data" -k 3 --regulation GDPR

# Ask the full RAG agent (retrieval + grading + grounded answer + citations)
python -m scripts.ask "What is the lawful basis for processing employee data?"
python -m scripts.ask "data retention limits" --regulation GDPR

# Audit a document against the GDPR checkpoints
python -m scripts.audit data/samples/employment_contract.txt
```

### API

Run the server from `Compliance-RAG/backend/` with the venv active:

```bash
uvicorn app.api:app --reload
```

| Method | Route     | Purpose |
|--------|-----------|---------|
| `GET`  | `/health` | Health check |
| `POST` | `/query`  | Ask the RAG agent. Body: `{ question, regulation?, finding_context? }` |
| `POST` | `/audit`  | Upload a PDF/TXT contract; returns a structured `AuditReport` |

`finding_context` is optional. When present (populated by the "Ask a follow-up"
handoff), it is injected into the generation prompt as **untrusted reference
context** so answers stay grounded in retrieved regulation chunks. When absent,
the generation prompt is byte-identical to the plain Ask flow.

## Tests

```bash
cd Compliance-RAG/backend
pytest
```

## Project layout

```
german-compliance-agent/
└── Compliance-RAG/
    ├── backend/
    │   ├── app/
    │   │   ├── api.py              # FastAPI: /health, /query, /audit
    │   │   ├── config.py           # env settings (pydantic-settings)
    │   │   ├── db.py               # psycopg connection
    │   │   ├── embeddings.py       # Gemini embedder
    │   │   ├── llm.py              # Groq LLM
    │   │   ├── retrieval.py        # similarity_search over match_chunks
    │   │   ├── ingestion/          # loaders, chunker, pipeline
    │   │   ├── agent/              # LangGraph: graph, nodes, state, prompts
    │   │   └── audit/              # checkpoints, engine, schema
    │   ├── scripts/                # ingest, search, ask, audit, fetch_gdpr
    │   ├── data/                   # corpus/ (regulations) + samples/
    │   └── tests/
    ├── frontend/                   # Next.js app (ask + audit pages, components)
    └── supabase/schema.sql
```

## How the Ask agent works

`run_agent` streams a LangGraph state machine:

```
retrieve → grade_documents → (decide) ─┬─ generate → (grade_generation) ─┬─ END
                                       │                                 ├─ generate (regenerate)
                                       └─ transform_query → retrieve      └─ transform_query → retrieve
```

- **retrieve** — embed the question (Gemini) and pull top-k chunks via `match_chunks`.
- **grade_documents** — the LLM keeps only chunks relevant to the question.
- **transform_query** — if too few relevant chunks, rewrite the query and retry (bounded).
- **generate** — produce a grounded answer with `[REGULATION Article]` citations.
- **grade_generation** — check the answer is grounded and actually addresses the
  question; regenerate or re-retrieve if not (bounded).

## How the Audit works

`run_audit` walks a set of curated GDPR checkpoints. For each obligation it
retrieves the relevant contract clauses (filtered to the uploaded document) plus
the regulation text, then asks the LLM for a structured `AuditFindingAssessment`.
The contract excerpt in each finding is validated to be a **verbatim** quote from
the upload (never paraphrased or invented). The result is an `AuditReport` sorted
by status and severity.
