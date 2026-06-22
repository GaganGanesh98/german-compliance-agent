# GDPR Compliance Agent — Frontend

Next.js frontend for the compliance RAG backend: **Ask** (agentic Q&A) and **Audit** (document upload + severity-ranked report).

## Setup

```bash
cp .env.local.example .env.local
npm install
```

## Dev workflow

Run backend and frontend together:

```bash
# terminal 1
cd ../backend && source .venv/bin/activate && uvicorn app.api:app --reload

# terminal 2
cd frontend && npm run dev   # http://localhost:3000
```

`.env.local`:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

CORS on the backend already allows all origins in development.

## Pages

- `/` — landing page with links to Ask and Audit
- `/ask` — question form, cited answers, collapsible sources & agent trace
- `/audit` — file upload, summary chips, severity-ranked finding cards

## Scripts

```bash
npm run dev      # development server
npm run build    # production build
npm run start    # production server
npm run lint     # ESLint
```
