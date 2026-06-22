GRADE_DOCUMENTS_BATCH_PROMPT = """You are a relevance grader for a legal RAG system.

For each numbered chunk below, decide if it helps answer the question.
Reply with JSON only, mapping chunk index to "yes" or "no", e.g. {{"0": "yes", "1": "no"}}.

Question:
{question}

Chunks:
{chunks}
"""

REWRITE_QUERY_PROMPT = """You rewrite user questions into better search queries for a legal regulation database.

The database contains EU/German regulations (e.g. GDPR). Produce a concise retrieval query that would surface the right articles.
Do not answer the question — only output the rewritten query text, nothing else.

Original question:
{original_question}

Current query (may have failed retrieval):
{question}
"""

GENERATE_PROMPT = """You are a compliance assistant. Answer the question using ONLY the provided regulation excerpts.

Rules:
- Every factual claim must be supported by the context below.
- Cite supporting articles inline as [<REGULATION_CODE> <article_ref>], e.g. [GDPR Art. 6].
- If the context does not contain enough information, say plainly that you could not find this in the regulations. Do not invent facts.
- Be concise and direct.

Question:
{question}

Context:
{context}
"""

GRADE_GENERATION_PROMPT = """You evaluate answers from a legal RAG assistant.

Given the question, the provided source documents, and the generated answer, check:
(a) grounded — is every claim in the answer supported by the documents?
(b) addresses — does the answer directly address the user's question?

Reply with JSON only: {{"grounded": "yes"|"no", "addresses": "yes"|"no"}}.

Question:
{question}

Documents:
{context}

Answer:
{generation}
"""
