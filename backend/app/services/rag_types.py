from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID


RAGConfidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    document_title: str
    filename: str
    chunk_index: int
    content: str
    score: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RerankedChunk(RetrievedChunk):
    pass


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    confidence: RAGConfidence
    used_source_numbers: list[int]
    context_source_count: int
