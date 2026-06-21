from app.ingestion.chunker import chunk_text


SAMPLE_TEXT = """
Preamble text before articles.

Article 5
Principles relating to processing of personal data.
Personal data shall be processed lawfully, fairly and in a transparent manner.

Article 6
Lawfulness of processing.
Processing shall be lawful only if at least one of the following applies:
(a) the data subject has given consent;
(b) processing is necessary for the performance of a contract.

§ 1
This is a German section marker for testing.
"""


def test_chunker_splits_articles_with_refs() -> None:
    chunks = chunk_text(SAMPLE_TEXT)

    assert len(chunks) >= 3
    article_refs = [chunk.article_ref for chunk in chunks]
    assert "Art. 5" in article_refs
    assert "Art. 6" in article_refs
    assert "§ 1" in article_refs

    art6_chunks = [chunk for chunk in chunks if chunk.article_ref == "Art. 6"]
    assert len(art6_chunks) >= 1
    assert "Lawfulness of processing" in art6_chunks[0].content


def test_chunker_assigns_sequential_indices() -> None:
    chunks = chunk_text(SAMPLE_TEXT)
    indices = [chunk.chunk_index for chunk in chunks]
    assert indices == list(range(len(chunks)))
