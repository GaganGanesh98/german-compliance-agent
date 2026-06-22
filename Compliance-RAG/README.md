# German Compliance Audit Agent

Phase 1 delivers a typed Python ingestion and retrieval pipeline for German/EU regulation documents. It loads PDFs or text files, chunks them by article, embeds them with **Google Gemini** (`gemini-embedding-001`), stores vectors in Supabase Postgres (pgvector), and retrieves relevant chunks from a CLI.

## Stack

- Python 3.11+
- FastAPI (foundation for later phases)
- Supabase Postgres + pgvector (direct `psycopg` connection)
- Google Gemini Embeddings (`gemini-embedding-001`, 1024-dim via MRL; free tier)

## Setup

1. Create and activate a virtual environment:

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy environment variables:

```bash
cp .env.example .env
```

Fill in:

- `DATABASE_URL` — use the **Session pooler** connection string from Supabase → Connect (IPv4-friendly).
- `GOOGLE_API_KEY` — from [Google AI Studio](https://aistudio.google.com/app/apikey) (embeddings).
- `GROQ_API_KEY` — reserved for Phase 2.

3. Apply the database schema in the Supabase SQL editor:

```bash
# paste contents of ../supabase/schema.sql
```

4. Add regulation files to `backend/data/corpus/` (e.g. `gdpr.pdf`, `gdpr.txt`).

## Usage

From `backend/` with the venv active:

```bash
# Ingest all PDF/txt files in data/corpus/
python -m scripts.ingest --source data/corpus

# Search ingested chunks
python -m scripts.search "What is the lawful basis for processing personal data?"
python -m scripts.search "lawful basis" -k 3 --regulation GDPR
```

## Tests

```bash
pytest
```

## Project layout

```
german-compliance-agent/
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── embeddings.py
│   │   ├── ingestion/
│   │   └── retrieval.py
│   ├── scripts/
│   ├── data/corpus/
│   └── tests/
├── supabase/schema.sql
└── README.md
```

## Phase 1 scope

This phase stops at retrieval. No agent, audit logic, UI, or Next.js.
