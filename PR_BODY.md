# Ask a follow-up about an audit finding

Lets a user reading an audit finding jump into the Ask chat with the finding's
context preloaded, so the answer is aware of the finding while staying grounded
in retrieved regulation chunks. Reuses `/query` and the existing LangGraph loop —
no new endpoint, services, or dependencies.

## Backend
- `QueryRequest.finding_context: str | None` → threaded through `run_agent` →
  seeded into `GraphState` → injected into `GENERATE_PROMPT` in the `generate`
  node. The self-corrective grading loop is untouched; grounding is still judged
  only against retrieved chunks.
- **Byte-identical-when-absent:** the finding block is emitted only when
  `finding_context` is set, so a normal Ask query produces exactly the same
  prompt as before (asserted in a test).
- **Prompt-injection hardening:** `finding_context` carries verbatim
  user-uploaded contract text, so it is framed as *untrusted reference data*,
  fenced with `BEGIN/END AUDIT FINDING (untrusted)` markers, and the model is
  told to treat its contents as data and ignore any embedded instructions.

## Frontend
- `FindingCard` gains an "Ask a follow-up" action that writes the finding context
  to **sessionStorage** and `router.push('/ask')` (same-tab navigation only).
- **Why sessionStorage, not a query param:** the excerpt is sensitive verbatim
  contract text — keeping it out of the URL avoids leaking it into history,
  referrer headers, and server logs. Shareability is moot (audit reports are
  ephemeral client state).
- `ChatPanel` reads **and clears** the handoff on mount (so a stale finding can't
  leak into a later unrelated chat), prefills a one-line templated question (no
  excerpt/rationale in the visible composer), threads `finding_context` through
  `/query`, and drops it after it is consumed.
- The mount read uses a **scoped `eslint-disable react-hooks/set-state-in-effect`**:
  it is a one-time hydration from a per-tab browser store that is unavailable
  during SSR, so it can't be a lazy `useState` initializer without a hydration
  mismatch.

## Verification
- `pytest`: 20 passed, 1 skipped (the live-key integration test).
- Live end-to-end on a local pgvector DB + real Gemini/Groq: upload → audit →
  "Ask a follow-up" → grounded answer citing `[GDPR Art. 13]` that addresses the
  finding's exact gaps; clear-on-mount confirmed; an embedded-instruction probe
  in `finding_context` was ignored by the live model.
