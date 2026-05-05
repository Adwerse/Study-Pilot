from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.document import Document
from app.services.document_chunker import DocumentChunker
from app.services.document_ingest_service import DocumentIngestService
from app.services.document_text_extractor import (
    ExtractedDocumentText,
    TextExtractionError,
)
from app.services.embedding_service import EmbeddingProviderError
from app.services.vector_index_service import VectorStoreUnavailableError


class FakeDocumentRepository:
    def __init__(self, document: Document):
        self.document = document
        self.chunks = []
        self.replace_calls = 0
        self.rollback_calls = 0

    async def get_by_id(self, document_id, user_id=None):
        _ = user_id
        if self.document.id == document_id:
            return self.document
        return None

    async def prepare_for_ingest(self, document):
        self.chunks = []
        document.status = "processing"
        document.error_message = None
        document.chunks_count = 0
        return document

    async def replace_chunks(self, document, chunks, embeddings):
        self.replace_calls += 1
        self.chunks = list(zip(chunks, embeddings, strict=True))
        document.status = "ready"
        document.error_message = None
        document.chunks_count = len(chunks)
        return document

    async def mark_failed(self, document_id, error_message):
        if self.document.id != document_id:
            return None
        self.chunks = []
        self.document.status = "failed"
        self.document.error_message = error_message
        self.document.chunks_count = 0
        return self.document

    async def rollback(self):
        self.rollback_calls += 1


class FakeTextExtractor:
    def __init__(self, extracted=None, error: Exception | None = None):
        self.extracted = extracted
        self.error = error
        self.called = False

    def extract(self, file_bytes, filename, content_type):
        assert file_bytes == b"document bytes"
        assert filename == "notes.txt"
        assert content_type == "text/plain"
        self.called = True
        if self.error is not None:
            raise self.error
        return self.extracted


class FakeEmbeddingService:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.texts = []

    async def embed_texts(self, texts):
        self.texts = texts
        if self.error is not None:
            raise self.error
        return [[float(index), 0.0, 1.0] for index, _ in enumerate(texts)]


class FakeVectorIndex:
    def __init__(
        self,
        repo: FakeDocumentRepository,
        error: Exception | None = None,
    ):
        self.repo = repo
        self.error = error
        self.upsert_called = False
        self.upsert_user_id = None
        self.upsert_document_id = None

    async def upsert_chunks(self, user_id, document_id, chunks, embeddings):
        self.upsert_called = True
        self.upsert_user_id = user_id
        self.upsert_document_id = document_id
        if self.error is not None:
            raise self.error
        document = await self.repo.get_by_id(document_id, user_id)
        await self.repo.replace_chunks(document, chunks, embeddings)


@pytest.fixture
def document() -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        id=uuid4(),
        user_id=uuid4(),
        title="Notes",
        filename="notes.txt",
        content_type="text/plain",
        size_bytes=64,
        source_type="upload",
        status="processing",
        chunks_count=0,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_ingest_document_success_updates_status_and_chunks(document):
    repo = FakeDocumentRepository(document)
    extractor = FakeTextExtractor(
        ExtractedDocumentText(
            text="First paragraph.\n\nSecond paragraph with enough text for chunking."
        )
    )
    embeddings = FakeEmbeddingService()
    vector_index = FakeVectorIndex(repo)
    service = DocumentIngestService(
        document_repository=repo,
        text_extractor=extractor,
        chunker=DocumentChunker(chunk_size_chars=40, chunk_overlap_chars=5),
        embedding_service=embeddings,
        vector_index=vector_index,
    )

    result = await service.ingest_document(document.id, b"document bytes")

    assert extractor.called is True
    assert embeddings.texts == [chunk.content for chunk, _ in repo.chunks]
    assert vector_index.upsert_called is True
    assert vector_index.upsert_user_id == document.user_id
    assert vector_index.upsert_document_id == document.id
    assert result.status == "ready"
    assert result.chunks_count == len(repo.chunks)
    assert result.error_message is None


@pytest.mark.asyncio
async def test_ingest_failure_in_embeddings_marks_document_failed(document):
    repo = FakeDocumentRepository(document)
    service = DocumentIngestService(
        document_repository=repo,
        text_extractor=FakeTextExtractor(ExtractedDocumentText(text="Useful text")),
        chunker=DocumentChunker(chunk_size_chars=100, chunk_overlap_chars=10),
        embedding_service=FakeEmbeddingService(
            error=EmbeddingProviderError("Embedding generation failed")
        ),
        vector_index=FakeVectorIndex(repo),
    )

    result = await service.ingest_document(document.id, b"document bytes")

    assert result.status == "failed"
    assert result.chunks_count == 0
    assert "Embedding generation failed" in result.error_message
    assert repo.rollback_calls == 1


@pytest.mark.asyncio
async def test_ingest_failure_in_vector_store_marks_document_failed(document):
    repo = FakeDocumentRepository(document)
    service = DocumentIngestService(
        document_repository=repo,
        text_extractor=FakeTextExtractor(ExtractedDocumentText(text="Useful text")),
        chunker=DocumentChunker(chunk_size_chars=100, chunk_overlap_chars=10),
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorIndex(
            repo, error=VectorStoreUnavailableError("Vector upsert failed")
        ),
    )

    result = await service.ingest_document(document.id, b"document bytes")

    assert result.status == "failed"
    assert result.chunks_count == 0
    assert "Vector upsert failed" in result.error_message
    assert repo.rollback_calls == 1


@pytest.mark.asyncio
async def test_ingest_failure_in_extraction_marks_document_failed(document):
    repo = FakeDocumentRepository(document)
    service = DocumentIngestService(
        document_repository=repo,
        text_extractor=FakeTextExtractor(
            error=TextExtractionError("Text documents must be UTF-8 encoded")
        ),
        chunker=DocumentChunker(chunk_size_chars=100, chunk_overlap_chars=10),
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorIndex(repo),
    )

    result = await service.ingest_document(document.id, b"document bytes")

    assert result.status == "failed"
    assert result.chunks_count == 0
    assert "UTF-8" in result.error_message


@pytest.mark.asyncio
async def test_retry_ingest_replaces_chunks_without_duplicates(document):
    repo = FakeDocumentRepository(document)
    service = DocumentIngestService(
        document_repository=repo,
        text_extractor=FakeTextExtractor(ExtractedDocumentText(text="One two three")),
        chunker=DocumentChunker(chunk_size_chars=100, chunk_overlap_chars=10),
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorIndex(repo),
    )

    first = await service.ingest_document(document.id, b"document bytes")
    first_count = len(repo.chunks)
    second = await service.ingest_document(document.id, b"document bytes")

    assert first.status == "ready"
    assert second.status == "ready"
    assert len(repo.chunks) == first_count
    assert repo.replace_calls == 2
