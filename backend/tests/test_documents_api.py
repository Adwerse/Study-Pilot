from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.api import documents as documents_api
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.document import Document, DocumentChunk


class FakeDocumentRepository:
    def __init__(self, documents: list[Document] | None = None):
        self.documents = documents or []
        self.chunks: list[DocumentChunk] = []
        self.created_document: Document | None = None
        self.created_user_id = None
        self.list_user_id = None
        self.get_user_id = None
        self.deleted_document_id = None
        self.deleted_chunks_for = None
        self.rollback_calls = 0

    async def create_document(
        self,
        user_id,
        title,
        filename,
        content_type,
        size_bytes,
        source_type,
        tags=None,
    ):
        now = datetime.now(timezone.utc)
        document = Document(
            id=uuid4(),
            user_id=user_id,
            title=title,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            source_type=source_type,
            status="processing",
            chunks_count=0,
            tags=tags,
            created_at=now,
            updated_at=now,
        )
        self.created_document = document
        self.created_user_id = user_id
        self.documents.append(document)
        return document

    async def list_by_user(self, user_id, limit=20, offset=0, status=None, q=None):
        self.list_user_id = user_id
        items = [document for document in self.documents if document.user_id == user_id]
        if status is not None:
            items = [document for document in items if document.status == status]
        if q is not None:
            lowered_q = q.lower()
            items = [
                document
                for document in items
                if lowered_q in document.title.lower()
                or lowered_q in document.filename.lower()
            ]
        items = sorted(items, key=lambda document: document.created_at, reverse=True)
        return items[offset : offset + limit], len(items)

    async def get_by_id(self, document_id, user_id=None):
        self.get_user_id = user_id
        for document in self.documents:
            if document.id != document_id:
                continue
            if user_id is not None and document.user_id != user_id:
                return None
            return document
        return None

    async def delete_chunks(self, document_id, user_id, commit=True):
        _ = commit
        self.deleted_chunks_for = (document_id, user_id)
        self.chunks = [
            chunk
            for chunk in self.chunks
            if chunk.document_id != document_id or chunk.user_id != user_id
        ]

    async def delete_document(self, document, commit=True):
        _ = commit
        self.deleted_document_id = document.id
        self.documents = [item for item in self.documents if item.id != document.id]

    async def rollback(self):
        self.rollback_calls += 1


class FakeVectorIndex:
    def __init__(self, repo: FakeDocumentRepository, error: Exception | None = None):
        self.repo = repo
        self.error = error
        self.calls = []

    async def delete_document(self, document_id, user_id):
        self.calls.append((document_id, user_id))
        if self.error is not None:
            raise self.error
        await self.repo.delete_chunks(document_id, user_id, commit=False)


class FakeDocumentIngestService:
    def __init__(self, repo: FakeDocumentRepository):
        self.repo = repo
        self.file_bytes = None

    async def ingest_document(self, document_id, file_bytes):
        self.file_bytes = file_bytes
        document = await self.repo.get_by_id(document_id)
        document.status = "ready"
        document.chunks_count = 1
        return document


@pytest.fixture(autouse=True)
def override_documents_dependencies(app):
    async def fake_current_user():
        return {"id": 123456, "username": "tester", "first_name": "Test"}

    async def fake_get_db():
        yield object()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_db] = fake_get_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_upload_txt_document_creates_user_scoped_document(client, monkeypatch):
    user_id = uuid4()
    repo = FakeDocumentRepository()
    ingest_service = FakeDocumentIngestService(repo)

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)
    monkeypatch.setattr(
        documents_api, "build_document_ingest_service", lambda db: ingest_service
    )

    response = await client.post(
        "/api/v1/documents/upload",
        data={"title": "My Notes", "tags": "ai, backend"},
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == str(repo.created_document.id)
    assert payload["status"] == "ready"
    assert payload["title"] == "My Notes"
    assert payload["filename"] == "notes.txt"
    assert payload["chunks_count"] == 1
    assert repo.created_user_id == user_id
    assert repo.created_document.tags == ["ai", "backend"]
    assert ingest_service.file_bytes == b"hello world"


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_file_type(client):
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.exe", b"hello", "application/octet-stream")},
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_rejects_empty_file(client):
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"", "text/plain")},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_rejects_too_large_file(client, monkeypatch):
    monkeypatch.setattr(documents_api.settings, "DOCUMENT_MAX_FILE_SIZE_BYTES", 5)

    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"123456", "text/plain")},
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_list_documents_returns_only_current_user_documents(client, monkeypatch):
    user_id = uuid4()
    other_user_id = uuid4()
    now = datetime.now(timezone.utc)
    own_document = Document(
        id=uuid4(),
        user_id=user_id,
        title="Mine",
        filename="mine.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=2,
        created_at=now,
        updated_at=now,
    )
    other_document = Document(
        id=uuid4(),
        user_id=other_user_id,
        title="Theirs",
        filename="theirs.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=1,
        created_at=now,
        updated_at=now,
    )
    repo = FakeDocumentRepository([own_document, other_document])

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)

    response = await client.get("/api/v1/documents")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == str(own_document.id)
    assert "content" not in payload["items"][0]
    assert "chunks" not in payload["items"][0]
    assert payload["items"][0]["content_type"] == "text/plain"
    assert payload["items"][0]["size_bytes"] == 12
    assert payload["items"][0]["error_message"] is None
    assert "updated_at" in payload["items"][0]
    assert repo.list_user_id == user_id


@pytest.mark.asyncio
async def test_list_documents_supports_limit_offset_status_and_q(client, monkeypatch):
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    older = Document(
        id=uuid4(),
        user_id=user_id,
        title="Python Notes",
        filename="python.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=2,
        error_message=None,
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )
    newer = Document(
        id=uuid4(),
        user_id=user_id,
        title="Failed Biology Notes",
        filename="biology.pdf",
        content_type="application/pdf",
        size_bytes=128,
        source_type="upload",
        status="failed",
        chunks_count=0,
        error_message="Traceback: provider key abc123 should stay short",
        created_at=now,
        updated_at=now,
    )
    repo = FakeDocumentRepository([older, newer])

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)

    paged_response = await client.get("/api/v1/documents?limit=1&offset=1")
    failed_response = await client.get("/api/v1/documents?status=failed")
    q_response = await client.get("/api/v1/documents?q=python")

    assert paged_response.status_code == 200
    assert paged_response.json()["items"][0]["id"] == str(older.id)
    assert failed_response.status_code == 200
    assert failed_response.json()["total"] == 1
    assert failed_response.json()["items"][0]["id"] == str(newer.id)
    assert (
        failed_response.json()["items"][0]["error_message"]
        == "Document processing failed"
    )
    assert q_response.status_code == 200
    assert q_response.json()["total"] == 1
    assert q_response.json()["items"][0]["id"] == str(older.id)


@pytest.mark.asyncio
async def test_get_document_returns_own_document(client, monkeypatch):
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid4(),
        user_id=user_id,
        title="Mine",
        filename="mine.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="processing",
        chunks_count=0,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    repo = FakeDocumentRepository([document])

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)

    response = await client.get(f"/api/v1/documents/{document.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(document.id)
    assert repo.get_user_id == user_id


@pytest.mark.asyncio
async def test_get_document_does_not_expose_other_users_document(client, monkeypatch):
    user_id = uuid4()
    other_user_id = uuid4()
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid4(),
        user_id=other_user_id,
        title="Theirs",
        filename="theirs.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=1,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    repo = FakeDocumentRepository([document])

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)

    response = await client.get(f"/api/v1/documents/{document.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_deletes_own_document_chunks_and_vectors(
    client, monkeypatch
):
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid4(),
        user_id=user_id,
        title="Mine",
        filename="mine.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=1,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document.id,
        user_id=user_id,
        chunk_index=0,
        content="private content",
        token_count=2,
        chunk_metadata={},
        embedding=[0.1, 0.2, 0.3],
        created_at=now,
    )
    repo = FakeDocumentRepository([document])
    repo.chunks = [chunk]
    vector_index = FakeVectorIndex(repo)

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)
    monkeypatch.setattr(
        documents_api, "build_vector_index_service", lambda repo_arg: vector_index
    )

    response = await client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 204
    assert vector_index.calls == [(document.id, user_id)]
    assert repo.deleted_chunks_for == (document.id, user_id)
    assert repo.deleted_document_id == document.id
    assert repo.documents == []
    assert repo.chunks == []


@pytest.mark.asyncio
async def test_delete_document_returns_404_for_foreign_document(client, monkeypatch):
    user_id = uuid4()
    other_user_id = uuid4()
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid4(),
        user_id=other_user_id,
        title="Theirs",
        filename="theirs.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=1,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    repo = FakeDocumentRepository([document])
    vector_index = FakeVectorIndex(repo)

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)
    monkeypatch.setattr(
        documents_api, "build_vector_index_service", lambda repo_arg: vector_index
    )

    response = await client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 404
    assert vector_index.calls == []
    assert repo.documents == [document]


@pytest.mark.asyncio
async def test_delete_document_vector_failure_keeps_document_and_chunks(
    client, monkeypatch
):
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid4(),
        user_id=user_id,
        title="Mine",
        filename="mine.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=1,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    chunk = DocumentChunk(
        id=uuid4(),
        document_id=document.id,
        user_id=user_id,
        chunk_index=0,
        content="private content",
        token_count=2,
        chunk_metadata={},
        embedding=[0.1, 0.2, 0.3],
        created_at=now,
    )
    repo = FakeDocumentRepository([document])
    repo.chunks = [chunk]
    vector_index = FakeVectorIndex(repo, error=RuntimeError("qdrant down"))

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)
    monkeypatch.setattr(
        documents_api, "build_vector_index_service", lambda repo_arg: vector_index
    )

    response = await client.delete(f"/api/v1/documents/{document.id}")

    assert response.status_code == 503
    assert response.json()["detail"] == "Vector index cleanup failed"
    assert repo.rollback_calls == 1
    assert repo.documents == [document]
    assert repo.chunks == [chunk]


@pytest.mark.asyncio
async def test_delete_document_repeated_delete_returns_404(client, monkeypatch):
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    document = Document(
        id=uuid4(),
        user_id=user_id,
        title="Mine",
        filename="mine.txt",
        content_type="text/plain",
        size_bytes=12,
        source_type="upload",
        status="ready",
        chunks_count=0,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    repo = FakeDocumentRepository([document])
    vector_index = FakeVectorIndex(repo)

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(documents_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(documents_api, "build_document_repository", lambda db: repo)
    monkeypatch.setattr(
        documents_api, "build_vector_index_service", lambda repo_arg: vector_index
    )

    first_response = await client.delete(f"/api/v1/documents/{document.id}")
    second_response = await client.delete(f"/api/v1/documents/{document.id}")

    assert first_response.status_code == 204
    assert second_response.status_code == 404
