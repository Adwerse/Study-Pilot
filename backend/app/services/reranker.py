import logging
import re
from typing import Protocol

from app.services.rag_types import RerankedChunk, RetrievedChunk


logger = logging.getLogger(__name__)

TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


class RerankProviderProtocol(Protocol):
    async def rerank(
        self,
        question: str,
        rewritten_query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RerankedChunk]: ...


class Reranker:
    def __init__(self, provider: RerankProviderProtocol | None = None):
        self.provider = provider

    async def rerank(
        self,
        question: str,
        rewritten_query: str,
        chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RerankedChunk]:
        if not chunks:
            return []

        limit = max(1, min(top_k, len(chunks)))
        if self.provider is not None:
            try:
                provided = await self.provider.rerank(
                    question=question,
                    rewritten_query=rewritten_query,
                    chunks=chunks,
                    top_k=limit,
                )
                return provided[:limit]
            except Exception:
                logger.warning(
                    "Rerank provider failed; using vector order", exc_info=True
                )
                return [
                    self._from_retrieved(chunk, chunk.score) for chunk in chunks[:limit]
                ]

        query_text = f"{question} {rewritten_query}"
        scored = [
            self._from_retrieved(
                chunk,
                self._combine_scores(
                    vector_score=chunk.score,
                    lexical_score=self._lexical_score(query_text, chunk.content),
                ),
            )
            for chunk in chunks
        ]
        return sorted(scored, key=lambda chunk: chunk.score, reverse=True)[:limit]

    @staticmethod
    def _from_retrieved(chunk: RetrievedChunk, score: float) -> RerankedChunk:
        return RerankedChunk(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            filename=chunk.filename,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=max(0.0, min(float(score), 1.0)),
            metadata=chunk.metadata,
        )

    @staticmethod
    def _lexical_score(query: str, content: str) -> float:
        query_tokens = {
            token for token in TOKEN_PATTERN.findall(query.lower()) if len(token) > 2
        }
        if not query_tokens:
            return 0.0

        content_tokens = {
            token for token in TOKEN_PATTERN.findall(content.lower()) if len(token) > 2
        }
        if not content_tokens:
            return 0.0

        return len(query_tokens & content_tokens) / len(query_tokens)

    @staticmethod
    def _combine_scores(vector_score: float, lexical_score: float) -> float:
        final_score = 0.7 * vector_score + 0.3 * lexical_score
        return max(0.0, min(final_score, 1.0))
