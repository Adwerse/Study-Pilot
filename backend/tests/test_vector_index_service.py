from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.document import Document
from app.services.document_chunker import DocumentChunkInput
from app.services.vector_index_service import (
    VectorDimensionMismatchError,
    VectorIndexService,
    VectorStoreError,
)


class FakeDBResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.query = None

    async def execute(self, query):
        self.query = query
        return FakeDBResult(self.rows)


class FakeChunkRow:
    def __init__(self, user_id, document_id):
        self.id = uuid4()
        self.user_id = user_id
        self.document_id = document_id
        self.chunk_index = 2
        self.content = "Matched private content"
        self.chunk_metadata = {"page_number": 4}


class FakeDocumentRepository:
    def __init__(self, document=None, db=None):
        self.document = document
        self.db = db or FakeDB()
        self.replace_calls = []
        self.deleted_chunks_for = None

    async def get_by_id(self, document_id, user_id=None):
        if self.document is None:
            return None
        if self.document.id != document_id:
            return None
        if user_id is not None and self.document.user_id != user_id:
            return None
        return self.document

    async def replace_chunks(self, document, chunks, embeddings):
        self.replace_calls.append((document, chunks, embeddings))

    async def delete_chunks(self, document_id, user_id, commit=True):
        self.deleted_chunks_for = (document_id, user_id, commit)


def make_document(user_id=None, document_id=None):
    now = datetime.now(timezone.utc)
    return Document(
        id=document_id or uuid4(),
        user_id=user_id or uuid4(),
        title="Notes",
        filename="notes.txt",
        content_type="text/plain",
        size_bytes=10,
        source_type="upload",
        status="processing",
        chunks_count=0,
        created_at=now,
        updated_at=now,
    )


def make_chunk(index=0):
    return DocumentChunkInput(
        chunk_index=index,
        content=f"Chunk {index}",
        token_count=2,
        metadata={"page_number": index + 1},
    )


@pytest.mark.asyncio
async def test_upsert_chunks_validates_embedding_dimensions():
    document = make_document()
    repo = FakeDocumentRepository(document=document)
    service = VectorIndexService(repo, embedding_dimensions=3)

    await service.upsert_chunks(
        user_id=document.user_id,
        document_id=document.id,
        chunks=[make_chunk()],
        embeddings=[[0.1, 0.2, 0.3]],
    )

    assert len(repo.replace_calls) == 1

    with pytest.raises(VectorDimensionMismatchError):
        await service.upsert_chunks(
            user_id=document.user_id,
            document_id=document.id,
            chunks=[make_chunk()],
            embeddings=[[0.1, 0.2]],
        )


@pytest.mark.asyncio
async def test_upsert_chunks_rejects_count_mismatch():
    document = make_document()
    service = VectorIndexService(
        FakeDocumentRepository(document=document),
        embedding_dimensions=3,
    )

    with pytest.raises(VectorStoreError):
        await service.upsert_chunks(
            user_id=document.user_id,
            document_id=document.id,
            chunks=[make_chunk(), make_chunk(1)],
            embeddings=[[0.1, 0.2, 0.3]],
        )


@pytest.mark.asyncio
async def test_search_requires_user_filter_and_supports_document_ids_filter():
    user_id = uuid4()
    document_id = uuid4()
    chunk = FakeChunkRow(user_id=user_id, document_id=document_id)
    db = FakeDB(rows=[(chunk, "Doc", "doc.pdf", 0.15)])
    repo = FakeDocumentRepository(db=db)
    service = VectorIndexService(repo, embedding_dimensions=3)

    results = await service.search(
        user_id=user_id,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=8,
        document_ids=[document_id],
    )

    compiled_query = str(db.query)
    assert "document_chunks.user_id" in compiled_query
    assert "documents.user_id" in compiled_query
    assert "documents.status" in compiled_query
    assert "document_chunks.document_id" in compiled_query
    assert len(results) == 1
    assert results[0].document_id == document_id
    assert results[0].document_title == "Doc"
    assert results[0].filename == "doc.pdf"
    assert results[0].score == pytest.approx(0.85)


@pytest.mark.asyncio
async def test_search_validates_query_embedding_dimension():
    service = VectorIndexService(FakeDocumentRepository(), embedding_dimensions=3)

    with pytest.raises(VectorDimensionMismatchError):
        await service.search(
            user_id=uuid4(),
            query_embedding=[0.1, 0.2],
            top_k=8,
        )


@pytest.mark.asyncio
async def test_delete_document_uses_user_id_and_document_id():
    repo = FakeDocumentRepository()
    service = VectorIndexService(repo, embedding_dimensions=3)
    user_id = uuid4()
    document_id = uuid4()

    await service.delete_document(user_id=user_id, document_id=document_id)

    assert repo.deleted_chunks_for == (document_id, user_id, False)
