"""Fetch the full GDPR as clean, article-structured text.

Scrapes the per-article pages on gdpr-info.eu (Articles 1-99) and writes a
single file whose layout matches what ``app.ingestion.chunker`` expects: each
article begins with an ``Article N`` line so boundary detection and citation
(``article_ref``) work reliably. This avoids PDF-extraction artefacts that break
article-boundary detection.

Usage:
    python -m scripts.fetch_gdpr                 # -> data/corpus/gdpr.txt
    python -m scripts.fetch_gdpr --out path.txt
    python -m scripts.fetch_gdpr --max-article 10   # smaller run for testing

The text is the official GDPR (Regulation (EU) 2016/679), public legislation.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# Matches an "Art. 6 GDPR ..." title repetition at the start of a body block.
TITLE_PREFIX = re.compile(r"^\s*Art\.?\s*\d+\s*GDPR\b", re.IGNORECASE)
# Strips the "Art. 6 GDPR – " prefix from the page title to leave the subtitle.
TITLE_STRIP = re.compile(r"^\s*Art\.?\s*\d+\s*(?:GDPR)?\s*[–\-:]*\s*", re.IGNORECASE)

BASE_URL = "https://gdpr-info.eu/art-{n}-gdpr/"
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "data" / "corpus" / "gdpr.txt"
HEADERS = {"User-Agent": "german-compliance-agent/0.1 (corpus fetch)"}
TOTAL_ARTICLES = 99


def _extract_article(html: str) -> tuple[str, str] | None:
    """Return (title, body) for one article page, or None if not parseable."""
    soup = BeautifulSoup(html, "html.parser")

    # Title, e.g. "Art. 6 GDPR – Lawfulness of processing"
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""

    # Main body. gdpr-info.eu uses div.entry-content; fall back to the largest
    # text block if the class ever changes.
    content = soup.select_one("div.entry-content")
    if content is None:
        candidates = soup.find_all(["div", "article", "main"])
        content = max(candidates, key=lambda el: len(el.get_text()), default=None)
    if content is None:
        return None

    # Drop nav/sidebar/script noise.
    for tag in content.find_all(["script", "style", "nav", "aside", "form"]):
        tag.decompose()

    # Extract block-level text only, joining inline elements (e.g. cross-reference
    # links to "Article 23") with spaces so they do NOT land on their own line.
    # Otherwise the chunker mistakes an in-body cross-reference for a new article
    # boundary and mis-attributes the citation. Stop at the "Suitable Recitals"
    # appendix, which is cross-reference/nav material, not the binding article text.
    nav_crumbs = {"gdpr", "table of contents", "report error", "→", "↑"}
    raw_blocks: list[str] = []
    for el in content.find_all(["p", "li", "h2", "h3", "h4", "blockquote"]):
        line = el.get_text(" ", strip=True)
        if not line:
            continue
        if line.lower().startswith("suitable recitals"):
            break
        if line.lower() in nav_crumbs:
            continue
        if TITLE_PREFIX.match(line):  # "Art. 6 GDPR ..." title repetition
            continue
        raw_blocks.append(line)

    # Drop blocks fully contained in a longer block. gdpr-info.eu renders some
    # paragraphs both as one combined block and as individual list items; keep
    # the richest version and discard the fragments to avoid duplicate chunks.
    kept: list[str] = []
    for line in sorted(raw_blocks, key=len, reverse=True):
        if any(line in longer for longer in kept):
            continue
        kept.append(line)
    order = {line: i for i, line in enumerate(raw_blocks)}
    kept.sort(key=lambda ln: order[ln])

    body = "\n".join(kept)
    if not body:
        return None
    return title, body


def fetch_gdpr(out: Path, max_article: int = TOTAL_ARTICLES, delay: float = 0.5) -> int:
    sections: list[str] = [
        "REGULATION (EU) 2016/679 — GENERAL DATA PROTECTION REGULATION (GDPR)",
        "",
    ]
    fetched = 0
    with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
        for n in range(1, max_article + 1):
            url = BASE_URL.format(n=n)
            try:
                resp = client.get(url)
            except httpx.HTTPError as exc:
                print(f"  ! Art. {n}: request failed ({exc})", file=sys.stderr)
                continue
            if resp.status_code != 200:
                print(f"  ! Art. {n}: HTTP {resp.status_code}, skipping", file=sys.stderr)
                continue

            parsed = _extract_article(resp.text)
            if parsed is None:
                print(f"  ! Art. {n}: could not parse, skipping", file=sys.stderr)
                continue

            title, body = parsed
            # Force a clean "Article N" header line for the chunker, keeping the
            # human title underneath.
            heading = f"Article {n}"
            subtitle = TITLE_STRIP.sub("", title).strip()
            sections.append(heading)
            if subtitle and subtitle.lower() != heading.lower():
                sections.append(subtitle)
            sections.append(body)
            sections.append("")
            fetched += 1
            print(f"  + Art. {n}: {subtitle[:60]}")
            time.sleep(delay)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(sections), encoding="utf-8")
    return fetched


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch full GDPR text into the corpus.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-article", type=int, default=TOTAL_ARTICLES)
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    args = parser.parse_args()

    print(f"Fetching GDPR Articles 1-{args.max_article} -> {args.out}")
    count = fetch_gdpr(args.out, max_article=args.max_article, delay=args.delay)
    print(f"Done. Wrote {count} articles to {args.out}")
    if count < args.max_article * 0.8:
        print(
            "Warning: fewer articles than expected were fetched — "
            "check the site structure or your connection.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
