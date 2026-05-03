import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.services.rag_types import RetrievedChunk


logger = logging.getLogger(__name__)


class VectorSearchError(Exception):
    pass


class VectorSearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        user_id: UUID,
        query_embedding: list[float],
        document_ids: list[UUID] | None = None,
        top_k: int = 8,
    ) -> list[RetrievedChunk]:
        if not query_embedding:
            return []

        limit = max(1, min(top_k, 20))
        distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        query = (
            select(DocumentChunk, Document.title, Document.filename, distance)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                DocumentChunk.user_id == user_id,
                Document.user_id == user_id,
                Document.status == "ready",
            )
            .order_by(distance.asc())
            .limit(limit)
        )
        if document_ids is not None:
            if not document_ids:
                return []
            query = query.where(DocumentChunk.document_id.in_(document_ids))

        try:
            result = await self.db.execute(query)
        except SQLAlchemyError as exc:
            logger.exception("Vector search failed user_id=%s", user_id)
            raise VectorSearchError("Vector search failed") from exc

        chunks: list[RetrievedChunk] = []
        for chunk, title, filename, raw_distance in result.all():
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=title,
                    filename=filename,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=self._distance_to_score(raw_distance),
                    metadata=chunk.chunk_metadata or {},
                )
            )
        return chunks

    @staticmethod
    def _distance_to_score(distance: float | None) -> float:
        if distance is None:
            return 0.0

        score = 1.0 - float(distance)
        return max(0.0, min(score, 1.0))
