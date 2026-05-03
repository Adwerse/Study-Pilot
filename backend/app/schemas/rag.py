from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.config import settings


RAGConfidence = Literal["low", "medium", "high"]


class RAGQuestionRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    document_ids: list[UUID] | None = None
    top_k: int = Field(
        default=settings.RAG_TOP_K_DEFAULT,
        ge=1,
        le=20,
        validate_default=True,
    )
    rerank_top_k: int = Field(
        default=settings.RAG_RERANK_TOP_K_DEFAULT,
        ge=1,
        le=10,
        validate_default=True,
    )

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Question must be at least 2 characters long")
        return normalized

    @field_validator("document_ids")
    @classmethod
    def dedupe_document_ids(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is None:
            return None

        deduped = list(dict.fromkeys(value))
        return deduped or None


class RAGSource(BaseModel):
    document_id: UUID
    document_title: str
    filename: str
    chunk_id: UUID
    chunk_index: int
    score: float = Field(ge=0.0, le=1.0)
    page_number: int | None = None
    snippet: str


class RAGAnswer(BaseModel):
    answer: str
    sources: list[RAGSource]
    rewritten_query: str
    confidence: RAGConfidence
