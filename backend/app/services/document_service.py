from uuid import UUID

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.vector_index_service import VectorIndexService


class DocumentNotFoundError(Exception):
    pass


class VectorIndexCleanupError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        vector_index: VectorIndexService,
    ):
        self.document_repository = document_repository
        self.vector_index = vector_index

    async def list_user_documents(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        status: str | None = None,
        q: str | None = None,
    ) -> tuple[list[Document], int]:
        return await self.document_repository.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status,
            q=q,
        )

    async def get_user_document_or_404(
        self,
        user_id: UUID,
        document_id: UUID,
    ) -> Document:
        document = await self.document_repository.get_by_id(
            document_id=document_id,
            user_id=user_id,
        )
        if document is None:
            raise DocumentNotFoundError("Document not found")
        return document

    async def delete_user_document(
        self,
        user_id: UUID,
        document_id: UUID,
    ) -> None:
        document = await self.get_user_document_or_404(
            user_id=user_id,
            document_id=document_id,
        )

        try:
            await self.vector_index.delete_document(document.id, user_id)
        except Exception as exc:
            await self.document_repository.rollback()
            raise VectorIndexCleanupError("Vector index cleanup failed") from exc

        await self.document_repository.delete_document(document)
