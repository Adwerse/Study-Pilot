from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.document_repository import DocumentRepository
from app.services.rag_types import RetrievedChunk
from app.services.vector_index_service import (
    VectorIndexService,
    VectorStoreError,
)


class VectorSearchError(VectorStoreError):
    pass


class VectorSearchService:
    """Compatibility wrapper; new code should depend on VectorIndexService."""

    def __init__(self, db: AsyncSession):
        self.vector_index = VectorIndexService(DocumentRepository(db))

    async def search(
        self,
        user_id: UUID,
        query_embedding: list[float],
        document_ids: list[UUID] | None = None,
        top_k: int = 8,
    ) -> list[RetrievedChunk]:
        try:
            return await self.vector_index.search(
                user_id=user_id,
                query_embedding=query_embedding,
                top_k=top_k,
                document_ids=document_ids,
            )
        except VectorStoreError as exc:
            raise VectorSearchError("Vector search failed") from exc
