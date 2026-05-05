import logging
from uuid import UUID

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.services.document_chunker import (
    DocumentChunker,
    DocumentChunkingError,
    DocumentChunkInput,
)
from app.services.document_text_extractor import (
    DocumentTextExtractor,
    ExtractedPageText,
    EmptyDocumentError,
    TextExtractionError,
    UnsupportedFileTypeError,
)
from app.services.embedding_service import EmbeddingProviderError, EmbeddingService
from app.services.vector_index_service import VectorIndexService, VectorStoreError


logger = logging.getLogger(__name__)


class DocumentIngestNotFoundError(Exception):
    pass


class DocumentIngestService:
    def __init__(
        self,
        document_repository: DocumentRepository,
        text_extractor: DocumentTextExtractor | None = None,
        chunker: DocumentChunker | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_index: VectorIndexService | None = None,
    ):
        self.document_repository = document_repository
        self.text_extractor = text_extractor or DocumentTextExtractor()
        self.chunker = chunker or DocumentChunker()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_index = vector_index or VectorIndexService(document_repository)

    async def ingest_document(self, document_id: UUID, file_bytes: bytes) -> Document:
        document = await self.document_repository.get_by_id(document_id)
        if document is None:
            raise DocumentIngestNotFoundError("Document not found")

        await self.document_repository.prepare_for_ingest(document)

        try:
            extracted = self.text_extractor.extract(
                file_bytes=file_bytes,
                filename=document.filename,
                content_type=document.content_type,
            )
            chunks = self._build_chunks(document, extracted.pages, extracted.text)
            if not chunks:
                raise EmptyDocumentError("Document does not contain extractable text")

            embeddings = await self.embedding_service.embed_texts(
                [chunk.content for chunk in chunks]
            )
            await self.vector_index.upsert_chunks(
                user_id=document.user_id,
                document_id=document.id,
                chunks=chunks,
                embeddings=embeddings,
            )
            updated_document = await self.document_repository.get_by_id(document.id)
            if updated_document is None:
                raise DocumentIngestNotFoundError("Document not found")
            return updated_document
        except (
            UnsupportedFileTypeError,
            EmptyDocumentError,
            TextExtractionError,
            DocumentChunkingError,
            EmbeddingProviderError,
            VectorStoreError,
        ) as exc:
            logger.exception(
                "Document ingest failed document_id=%s user_id=%s",
                document.id,
                document.user_id,
            )
            return await self._fail_document(document.id, str(exc))
        except Exception:
            logger.exception(
                "Unexpected document ingest failure document_id=%s user_id=%s",
                document.id,
                document.user_id,
            )
            return await self._fail_document(document.id, "Document processing failed")

    def _build_chunks(
        self,
        document: Document,
        pages: list[ExtractedPageText] | None,
        text: str,
    ) -> list[DocumentChunkInput]:
        base_metadata: dict[str, str | int | None] = {
            "filename": document.filename,
            "source_type": document.source_type,
        }

        if pages:
            page_chunks: list[DocumentChunkInput] = []
            for page in pages:
                page_metadata = {
                    **base_metadata,
                    "page_number": page.page_number,
                }
                page_chunks.extend(self.chunker.chunk_text(page.text, page_metadata))
            return self.chunker.reindex_chunks(page_chunks)

        return self.chunker.chunk_text(text, base_metadata)

    async def _fail_document(self, document_id: UUID, error_message: str) -> Document:
        await self.document_repository.rollback()
        document = await self.document_repository.mark_failed(
            document_id=document_id,
            error_message=self._sanitize_error_message(error_message),
        )
        if document is None:
            raise DocumentIngestNotFoundError("Document not found")
        return document

    @staticmethod
    def _sanitize_error_message(error_message: str) -> str:
        message = " ".join(error_message.split())
        if not message:
            return "Document processing failed"
        return message[:500]
