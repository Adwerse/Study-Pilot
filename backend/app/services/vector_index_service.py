import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.repositories.document_repository import DocumentRepository
from app.services.document_chunker import DocumentChunkInput
from app.services.rag_types import RetrievedChunk


logger = logging.getLogger(__name__)

VectorSearchResult = RetrievedChunk


class VectorStoreError(Exception):
    pass


class VectorStoreUnavailableError(VectorStoreError):
    pass


class VectorDimensionMismatchError(VectorStoreError):
    pass


class VectorIndexService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        provider: str | None = None,
        embedding_dimensions: int | None = None,
    ):
        self.document_repository = document_repository
        self.provider = provider or settings.VECTOR_STORE_PROVIDER
        self.embedding_dimensions = (
            embedding_dimensions or settings.EMBEDDING_DIMENSIONS
        )

    async def upsert_chunks(
        self,
        user_id: UUID,
        document_id: UUID,
        chunks: list[DocumentChunkInput],
        embeddings: list[list[float]],
    ) -> None:
        self._ensure_pgvector_provider()
        self._validate_upsert_payload(chunks=chunks, embeddings=embeddings)
        document = await self.document_repository.get_by_id(
            document_id=document_id,
            user_id=user_id,
        )
        if document is None:
            raise VectorStoreError("Document not found for vector upsert")

        try:
            await self.document_repository.replace_chunks(document, chunks, embeddings)
        except SQLAlchemyError as exc:
            logger.exception(
                "Vector upsert failed user_id=%s document_id=%s chunks_count=%s",
                user_id,
                document_id,
                len(chunks),
            )
            raise VectorStoreUnavailableError("Vector upsert failed") from exc

    async def search(
        self,
        user_id: UUID,
        query_embedding: list[float],
        top_k: int | None = None,
        document_ids: list[UUID] | None = None,
    ) -> list[VectorSearchResult]:
        self._ensure_pgvector_provider()
        if not query_embedding:
            return []

        self._validate_embedding_dimension(query_embedding, context="query_embedding")
        limit = max(1, min(top_k or settings.VECTOR_SEARCH_TOP_K_DEFAULT, 20))
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
                DocumentChunk.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(limit)
        )

        if document_ids is not None:
            if not document_ids:
                return []
            query = query.where(DocumentChunk.document_id.in_(document_ids))

        try:
            result = await self.document_repository.db.execute(query)
        except SQLAlchemyError as exc:
            logger.exception("Vector search failed user_id=%s", user_id)
            raise VectorStoreUnavailableError("Vector search failed") from exc

        chunks: list[VectorSearchResult] = []
        for chunk, title, filename, raw_distance in result.all():
            score = self._distance_to_score(raw_distance)
            if score < settings.VECTOR_SEARCH_SCORE_THRESHOLD:
                continue
            chunks.append(
                VectorSearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=title,
                    filename=filename,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=score,
                    metadata=chunk.chunk_metadata or {},
                )
            )
        return chunks

    async def delete_document(self, user_id: UUID, document_id: UUID) -> None:
        self._ensure_pgvector_provider()
        try:
            await self.document_repository.delete_chunks(
                document_id=document_id,
                user_id=user_id,
                commit=False,
            )
        except SQLAlchemyError as exc:
            logger.exception(
                "Vector delete failed user_id=%s document_id=%s",
                user_id,
                document_id,
            )
            raise VectorStoreUnavailableError("Vector delete failed") from exc

    def _ensure_pgvector_provider(self) -> None:
        if self.provider != "pgvector":
            raise VectorStoreUnavailableError(
                f"VECTOR_STORE_PROVIDER={self.provider!r} is not supported by this build"
            )

    def _validate_upsert_payload(
        self,
        chunks: list[DocumentChunkInput],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise VectorStoreError("Chunks and embeddings counts do not match")

        for index, embedding in enumerate(embeddings):
            self._validate_embedding_dimension(embedding, context=f"embedding[{index}]")

    def _validate_embedding_dimension(
        self,
        embedding: list[float],
        context: str,
    ) -> None:
        if len(embedding) != self.embedding_dimensions:
            raise VectorDimensionMismatchError(
                f"{context} dimension {len(embedding)} does not match "
                f"EMBEDDING_DIMENSIONS={self.embedding_dimensions}"
            )

    @staticmethod
    def _distance_to_score(distance: float | None) -> float:
        if distance is None:
            return 0.0

        score = 1.0 - float(distance)
        return max(0.0, min(score, 1.0))
