"""HTTP endpoints for the TrackFlow knowledge base."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.rag.pipeline import query

router = APIRouter(tags=["rag"])


class RagQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=3, ge=1, le=10)


@router.post("/knowledge/query")
def ask_knowledge_base(request: RagQuestion):
    try:
        return {"answer": query(request.question)}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/rag/query", include_in_schema=False)
def ask_knowledge_base_legacy(request: RagQuestion):
    return ask_knowledge_base(request)
