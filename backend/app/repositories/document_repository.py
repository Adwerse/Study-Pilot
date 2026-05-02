from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.services.document_chunker import DocumentChunkInput


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(
        self,
        user_id: UUID,
        title: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        source_type: str,
        tags: list[str] | None = None,
    ) -> Document:
        document = Document(
            user_id=user_id,
            title=title,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            source_type=source_type,
            status="processing",
            chunks_count=0,
            tags=tags or None,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_by_id(
        self, document_id: UUID, user_id: UUID | None = None
    ) -> Document | None:
        query = select(Document).where(Document.id == document_id)
        if user_id is not None:
            query = query.where(Document.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> tuple[list[Document], int]:
        filters = [Document.user_id == user_id]
        if status is not None:
            filters.append(Document.status == status)

        total_result = await self.db.execute(
            select(func.count()).select_from(Document).where(*filters)
        )
        total = int(total_result.scalar_one())

        items_result = await self.db.execute(
            select(Document)
            .where(*filters)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(items_result.scalars().all()), total

    async def prepare_for_ingest(self, document: Document) -> Document:
        await self.delete_chunks(document.id, document.user_id, commit=False)
        document.status = "processing"
        document.error_message = None
        document.chunks_count = 0
        document.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def replace_chunks(
        self,
        document: Document,
        chunks: list[DocumentChunkInput],
        embeddings: list[list[float]],
    ) -> Document:
        await self.delete_chunks(document.id, document.user_id, commit=False)

        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self.db.add(
                DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    chunk_metadata=chunk.metadata,
                    embedding=embedding,
                )
            )

        document.status = "ready"
        document.error_message = None
        document.chunks_count = len(chunks)
        document.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete_chunks(
        self, document_id: UUID, user_id: UUID, commit: bool = True
    ) -> None:
        await self.db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.user_id == user_id,
            )
        )
        if commit:
            await self.db.commit()

    async def mark_failed(
        self, document_id: UUID, error_message: str
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.status = "failed"
        document.error_message = error_message
        document.chunks_count = 0
        document.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def rollback(self) -> None:
        await self.db.rollback()
