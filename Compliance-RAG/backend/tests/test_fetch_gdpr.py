"""Tests for the GDPR corpus fetch parser (no network)."""

from app.ingestion.chunker import chunk_text
from scripts.fetch_gdpr import TITLE_STRIP, _extract_article

SAMPLE_HTML = """
<html><body>
<h1>Art. 6 GDPR – Lawfulness of processing</h1>
<div class="entry-content">
<p>→</p><p>GDPR</p><p>Table of contents</p>
<p>Art. 6 GDPR Lawfulness of processing</p>
<p>Processing shall be lawful only if at least one applies: consent given;
necessary for a contract; referred to in <a href="/art-23">Article 23</a>(1).</p>
<ul>
  <li>consent given</li>
  <li>necessary for a contract</li>
  <li>referred to in <a href="/art-23">Article 23</a>(1).</li>
</ul>
<h2>Suitable Recitals</h2>
<ul><li>(39) Principles</li></ul>
</div></body></html>
"""


def test_subtitle_strips_article_prefix() -> None:
    title = "Art. 6 GDPR – Lawfulness of processing"
    assert TITLE_STRIP.sub("", title).strip() == "Lawfulness of processing"
    # also works when the en-dash is absent
    assert TITLE_STRIP.sub("", "Art. 6 GDPR Lawfulness of processing").strip() == (
        "Lawfulness of processing"
    )


def test_extract_article_is_clean() -> None:
    title, body = _extract_article(SAMPLE_HTML)
    assert title.startswith("Art. 6 GDPR")
    # No nav crumbs, no recitals appendix.
    assert "Table of contents" not in body
    assert "Suitable Recitals" not in body
    # Duplicate list fragments removed (combined paragraph retained).
    assert body.count("consent given") == 1
    # No body line is a "Art. N GDPR ..." title repetition.
    assert not any(line.startswith("Art. 6 GDPR") for line in body.splitlines())


def test_no_false_boundaries_from_cross_references() -> None:
    title, body = _extract_article(SAMPLE_HTML)
    subtitle = TITLE_STRIP.sub("", title).strip()
    forced = f"Article 6\n{subtitle}\n{body}\n"
    chunks = chunk_text(forced)
    refs = sorted({c.article_ref for c in chunks if c.article_ref})
    assert refs == ["Art. 6"]
    assert min(c.token_count for c in chunks) > 3  # no isolated heading chunk
