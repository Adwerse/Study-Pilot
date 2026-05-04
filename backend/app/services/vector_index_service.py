from uuid import UUID

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_chunker import DocumentChunkInput


class VectorIndexService:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def upsert_chunks(
        self,
        document: Document,
        chunks: list[DocumentChunkInput],
        embeddings: list[list[float]],
    ) -> Document:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings counts do not match")
        return await self.document_repository.replace_chunks(
            document, chunks, embeddings
        )

    async def delete_document(self, document_id: UUID, user_id: UUID) -> None:
        await self.document_repository.delete_chunks(document_id, user_id, commit=False)
