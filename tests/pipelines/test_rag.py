from pathlib import Path
from types import SimpleNamespace

import pytest

from services.rag.chunking import chunk_document, load_corpus
from services.rag import pipeline


CORPUS = Path("docs/company-knowledge-base")


def test_corpus_contains_four_documents_and_three_chunks_each():
    chunks = load_corpus(CORPUS)

    assert len({chunk.source_document for chunk in chunks}) == 4
    for source in {chunk.source_document for chunk in chunks}:
        assert sum(chunk.source_document == source for chunk in chunks) >= 3


def test_chunking_rejects_short_documents(tmp_path):
    source = tmp_path / "short.es.md"
    source.write_text("# Short\nOnly one chunk.", encoding="utf-8")

    with pytest.raises(ValueError, match="at least three chunks"):
        chunk_document(source)


def test_chunking_keeps_sentence_boundaries(tmp_path):
    source = tmp_path / "sentences.es.md"
    source.write_text(
        "# Rules\n\nFirst complete rule. Second complete rule.\n\n"
        "Third complete rule.",
        encoding="utf-8",
    )

    chunks = chunk_document(source, max_chars=25)

    assert len(chunks) >= 3
    assert all(
        chunk.text.rstrip().endswith((".", "!", "?"))
        for chunk in chunks
    )


def test_retrieve_filters_scores_and_returns_only_payload(monkeypatch):
    points = [
        SimpleNamespace(score=0.91, payload={"text": "relevant"}),
        SimpleNamespace(score=0.21, payload={"text": "irrelevant"}),
    ]
    fake_qdrant = SimpleNamespace(
        query_points=lambda **kwargs: SimpleNamespace(points=points)
    )
    monkeypatch.setattr(pipeline, "_qdrant", lambda: fake_qdrant)
    monkeypatch.setattr(pipeline, "embed", lambda text: [0.1, 0.2])

    result = pipeline.retrieve("pregunta", k=5, min_score=0.5)

    assert result == [{"text": "relevant"}]
    assert "score" not in result[0]


def test_query_returns_generated_string_without_raw_chunks(monkeypatch):
    context = [{"source_document": "sla", "text": "SLA documentado"}]
    monkeypatch.setattr(pipeline, "retrieve", lambda question: context)
    monkeypatch.setattr(
        pipeline,
        "generate_answer",
        lambda question, retrieved: "Respuesta generada",
    )

    result = pipeline.query("¿Cuál es el SLA?")

    assert result == "Respuesta generada"
    assert isinstance(result, str)
    assert "SLA documentado" not in result
