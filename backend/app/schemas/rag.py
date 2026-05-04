from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import settings


RAGConfidence = Literal["low", "medium", "high"]


class AskRequest(BaseModel):
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

    @model_validator(mode="after")
    def validate_rerank_limit(self) -> Self:
        if self.rerank_top_k > self.top_k:
            raise ValueError("rerank_top_k must be less than or equal to top_k")
        return self


class RAGSource(BaseModel):
    document_id: UUID
    document_title: str
    filename: str
    chunk_id: UUID
    chunk_index: int
    score: float = Field(ge=0.0, le=1.0)
    page_number: int | None = None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    sources: list[RAGSource]
    rewritten_query: str
    confidence: RAGConfidence


RAGQuestionRequest = AskRequest
RAGAnswer = AskResponse
