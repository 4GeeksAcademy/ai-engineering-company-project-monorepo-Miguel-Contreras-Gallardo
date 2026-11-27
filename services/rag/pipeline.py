"""Qdrant retrieval and grounded generation for TrackFlow."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models

from services.rag.chunking import load_corpus

load_dotenv()

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "trackflow_knowledge")
FOURGEEKS_BASE_URL = os.getenv(
    "FOURGEEKS_BASE_URL", "https://llm.4geeks.ai/v1"
)
EMBEDDING_MODEL_ID = os.getenv(
    "EMBEDDING_MODEL_ID",
    "madrid-spain/openrouter/perplexity/pplx-embed-v1-0.6b",
)
GENERATION_MODEL_ID = os.getenv(
    "GENERATION_MODEL_ID",
    "madrid-spain/openrouter/deepseek/deepseek-v4-flash",
)
CORPUS_DIR = Path(os.getenv("RAG_CORPUS_DIR", "docs/company-knowledge-base"))


def _qdrant() -> QdrantClient:
    return QdrantClient(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY") or None,
    )


def _client() -> OpenAI:
    api_key = os.getenv("FOURGEEKS_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("FOURGEEKS_API_KEY or OPENAI_API_KEY is required.")
    return OpenAI(
        api_key=api_key,
        base_url=FOURGEEKS_BASE_URL or os.getenv("OPENAI_BASE_URL"),
    )


def setup(corpus_dir: Path = CORPUS_DIR) -> dict[str, Any]:
    """Create the collection and index the company corpus."""
    chunks = load_corpus(corpus_dir)
    vectors = [embed(chunk.text) for chunk in chunks]
    if not vectors:
        raise ValueError("The corpus produced no vectors.")
    client = _qdrant()
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=len(vectors[0]), distance=models.Distance.COSINE
        ),
    )
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{chunk.source_document}:{chunk.chunk_index}",
                )),
                vector=vector,
                payload={
                    "company": "trackflow",
                    "source_document": chunk.source_document,
                    "section": chunk.section,
                    "language": "es",
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ],
    )
    return {
        "collection": COLLECTION_NAME,
        "documents": len({chunk.source_document for chunk in chunks}),
        "chunks": len(chunks),
    }


def embed(text: str) -> list[float]:
    """Embed one text with the dedicated provider embedding model."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string.")
    response = _client().embeddings.create(
        model=EMBEDDING_MODEL_ID,
        input=text,
    )
    return response.data[0].embedding


def retrieve(
    query: str,
    *,
    k: int = 5,
    min_score: float = 0.35,
) -> list[dict[str, Any]]:
    """Retrieve payloads whose similarity score meets the threshold."""
    if not query.strip():
        raise ValueError("query must not be empty.")
    if k < 1:
        raise ValueError("k must be at least 1.")
    if not 0 <= min_score <= 1:
        raise ValueError("min_score must be between 0 and 1.")
    vector = embed(query)
    points = _qdrant().query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=k,
        with_payload=True,
    ).points
    return [
        dict(point.payload or {})
        for point in points
        if point.score is not None and point.score >= min_score
    ]


def generate_answer(question: str, context: list[dict[str, Any]]) -> str:
    """Generate a Spanish answer grounded only in retrieved payloads."""
    if not context:
        return "No hay información suficiente en la base de conocimiento."
    context_text = "\n\n".join(
        f"Fuente: {item.get('source_document', 'desconocida')}\n"
        f"Sección: {item.get('section', 'desconocida')}\n"
        f"{item.get('text', '')}"
        for item in context
    )
    response = _client().chat.completions.create(
        model=GENERATION_MODEL_ID,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un asistente comercial de TrackFlow. Responde en "
                    "español, de forma precisa y profesional, usando solo el "
                    "contexto proporcionado. No inventes tarifas, descuentos, "
                    "SLA, plazos ni excepciones. Las devoluciones "
                    "internacionales requieren gestión manual y cualquier "
                    "descuento de almacenamiento requiere aprobación. Si el "
                    "contexto no contiene la respuesta, indícalo claramente."
                ),
            },
            {
                "role": "user",
                "content": f"Contexto:\n{context_text}\n\nPregunta: {question}",
            },
        ],
    )
    return response.choices[0].message.content or ""


def query(question: str) -> str:
    """Retrieve context and return only the generated answer string."""
    return generate_answer(question, retrieve(question))
