"""Chunk the TrackFlow company knowledge base."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeChunk:
    source_document: str
    section: str
    chunk_index: int
    text: str


def _normalise_text(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip())


def _semantic_units(text: str, max_chars: int) -> list[str]:
    """Return paragraphs or complete sentences, never arbitrary substrings."""
    units: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = _normalise_text(paragraph)
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            units.append(paragraph)
            continue
        sentences = re.split(
            r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡0-9])",
            paragraph,
        )
        units.extend(sentence.strip() for sentence in sentences if sentence.strip())
    return units


def chunk_document(path: Path, max_chars: int = 500) -> list[KnowledgeChunk]:
    """Split Markdown by headings, paragraphs, and complete sentences."""
    content = _normalise_text(path.read_text(encoding="utf-8"))
    sections = re.split(r"(?m)^(?=#{1,6}\s)", content)
    chunks: list[KnowledgeChunk] = []
    for section in filter(None, sections):
        lines = section.splitlines()
        heading = next(
            (line.lstrip("# ").strip() for line in lines if line.startswith("#")),
            path.stem,
        )
        body = re.sub(r"(?m)^#{1,6}\s.*(?:\n|$)", "", section, count=1)
        units = _semantic_units(body, max_chars)
        current: list[str] = []
        current_length = 0
        for unit in units:
            separator_length = 2 if current else 0
            if current and current_length + separator_length + len(unit) > max_chars:
                chunks.append(
                    KnowledgeChunk(
                        path.stem,
                        heading,
                        len(chunks),
                        "\n\n".join(current),
                    )
                )
                current = []
                current_length = 0
            current.append(unit)
            current_length += (2 if len(current) > 1 else 0) + len(unit)
        if current:
            chunks.append(
                KnowledgeChunk(
                    path.stem,
                    heading,
                    len(chunks),
                    "\n\n".join(current),
                )
            )
    if len(chunks) < 3:
        raise ValueError(f"{path.name} must produce at least three chunks.")
    return chunks


def load_corpus(corpus_dir: Path) -> list[KnowledgeChunk]:
    paths = sorted(corpus_dir.glob("*.es.md"))
    if not paths:
        raise FileNotFoundError(f"No Spanish Markdown documents found in {corpus_dir}")
    return [chunk for path in paths for chunk in chunk_document(path)]
