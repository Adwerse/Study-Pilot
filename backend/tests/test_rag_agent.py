import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.api import ask as ask_api
from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.document import Document
from app.schemas.rag import RAGAnswer, RAGSource
from app.services.answer_generator import AnswerGenerator, LLMProviderError
from app.services.embedding_service import EmbeddingProviderError
from app.services.query_rewriter import QueryRewriter
from app.services.rag_agent import RAGAgent, RAGDocumentAccessError
from app.services.rag_types import RerankedChunk, RetrievedChunk
from app.services.reranker import Reranker
from app.services.vector_index_service import (
    VectorIndexService,
    VectorStoreUnavailableError,
)


@pytest.fixture(autouse=True)
def override_ask_dependencies(app):
    async def fake_current_user():
        return {"id": 123456, "username": "tester", "first_name": "Test"}

    async def fake_get_db():
        yield object()

    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_db] = fake_get_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


class FakeAPIAgent:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls = []

    async def answer_question(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


@pytest.mark.asyncio
async def test_post_ask_success(client, monkeypatch):
    user_id = uuid4()
    document_id = uuid4()
    chunk_id = uuid4()
    agent = FakeAPIAgent(
        RAGAnswer(
            answer="Дедлайн указан как пятница [1].",
            rewritten_query="дедлайн сроки",
            confidence="high",
            sources=[
                RAGSource(
                    document_id=document_id,
                    document_title="Plan",
                    filename="plan.pdf",
                    chunk_id=chunk_id,
                    chunk_index=0,
                    score=0.87,
                    page_number=3,
                    snippet="Submit the project by Friday.",
                )
            ],
        )
    )

    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return user_id

    monkeypatch.setattr(ask_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(ask_api, "build_rag_agent", lambda db: agent)

    response = await client.post(
        "/api/v1/ask",
        json={"question": "Что про дедлайны?", "top_k": 8, "rerank_top_k": 4},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Дедлайн указан как пятница [1]."
    assert payload["rewritten_query"] == "дедлайн сроки"
    assert payload["confidence"] == "high"
    assert payload["sources"][0]["page_number"] == 3
    assert agent.calls[0]["user_id"] == user_id


@pytest.mark.asyncio
async def test_post_ask_rejects_empty_question(client):
    response = await client.post("/api/v1/ask", json={"question": " "})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_ask_rejects_too_large_top_k(client):
    response = await client.post(
        "/api/v1/ask",
        json={"question": "valid question", "top_k": 21},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_ask_rejects_rerank_top_k_greater_than_top_k(client):
    response = await client.post(
        "/api/v1/ask",
        json={"question": "valid question", "top_k": 3, "rerank_top_k": 4},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_ask_rejects_other_users_document_id(client, monkeypatch):
    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return uuid4()

    monkeypatch.setattr(ask_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(
        ask_api,
        "build_rag_agent",
        lambda db: FakeAPIAgent(error=RAGDocumentAccessError("Document not found")),
    )

    response = await client.post(
        "/api/v1/ask",
        json={"question": "What is inside?", "document_ids": [str(uuid4())]},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_ask_maps_rag_provider_error_to_503(client, monkeypatch):
    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return uuid4()

    monkeypatch.setattr(ask_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(
        ask_api,
        "build_rag_agent",
        lambda db: FakeAPIAgent(
            error=EmbeddingProviderError("Embedding generation failed")
        ),
    )

    response = await client.post(
        "/api/v1/ask",
        json={"question": "What is inside?"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "RAG service is temporarily unavailable"


@pytest.mark.asyncio
async def test_post_ask_maps_vector_store_error_to_503(client, monkeypatch):
    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return uuid4()

    monkeypatch.setattr(ask_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(
        ask_api,
        "build_rag_agent",
        lambda db: FakeAPIAgent(
            error=VectorStoreUnavailableError("Vector search failed")
        ),
    )

    response = await client.post(
        "/api/v1/ask",
        json={"question": "What is inside?"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "RAG service is temporarily unavailable"


@pytest.mark.asyncio
async def test_post_ask_no_chunks_returns_honest_low_confidence(client, monkeypatch):
    async def fake_resolve_user_id(current_user, db):
        _ = current_user, db
        return uuid4()

    agent = FakeAPIAgent(
        RAGAnswer(
            answer="Я не нашёл релевантной информации в загруженных материалах.",
            rewritten_query="а что про экзамен",
            confidence="low",
            sources=[],
        )
    )
    monkeypatch.setattr(ask_api, "resolve_user_id", fake_resolve_user_id)
    monkeypatch.setattr(ask_api, "build_rag_agent", lambda db: agent)

    response = await client.post(
        "/api/v1/ask",
        json={"question": "а что про экзамен?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["confidence"] == "low"
    assert payload["sources"] == []
    assert "не нашёл" in payload["answer"]


@pytest.mark.asyncio
async def test_query_rewrite_success(monkeypatch):
    async def fake_complete(**kwargs):
        assert kwargs["temperature"] == 0.0
        return " дедлайны, сроки выполнения, due dates "

    monkeypatch.setattr("app.services.query_rewriter.complete", fake_complete)

    rewritten = await QueryRewriter(model="rewrite-model").rewrite(
        "а что там про дедлайны?"
    )

    assert rewritten == "дедлайны, сроки выполнения, due dates"


@pytest.mark.asyncio
async def test_query_rewrite_failure_falls_back_to_original(monkeypatch):
    async def fake_complete(**kwargs):
        _ = kwargs
        raise RuntimeError("provider down")

    monkeypatch.setattr("app.services.query_rewriter.complete", fake_complete)

    rewritten = await QueryRewriter().rewrite("а что там про дедлайны?")

    assert rewritten == "а что там про дедлайны?"


def make_retrieved_chunk(
    content: str,
    score: float = 0.5,
    user_document_id=None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=user_document_id or uuid4(),
        document_title="Notes",
        filename="notes.txt",
        chunk_index=0,
        content=content,
        score=score,
        metadata={"page_number": 2},
    )


@pytest.mark.asyncio
async def test_rerank_orders_better_lexical_match_higher():
    weak = make_retrieved_chunk("General lecture notes.", score=0.6)
    strong = make_retrieved_chunk(
        "Deadline and milestones are due on Friday.", score=0.5
    )

    reranked = await Reranker().rerank(
        question="What are the deadline milestones?",
        rewritten_query="deadline milestones due dates",
        chunks=[weak, strong],
        top_k=2,
    )

    assert reranked[0].chunk_id == strong.chunk_id
    assert reranked[0].score > reranked[1].score


@pytest.mark.asyncio
async def test_rerank_provider_failure_falls_back_to_vector_order():
    class FailingProvider:
        async def rerank(self, **kwargs):
            _ = kwargs
            raise RuntimeError("rerank failed")

    first = make_retrieved_chunk("First", score=0.8)
    second = make_retrieved_chunk("Second", score=0.9)

    reranked = await Reranker(provider=FailingProvider()).rerank(
        question="question",
        rewritten_query="query",
        chunks=[first, second],
        top_k=1,
    )

    assert len(reranked) == 1
    assert reranked[0].chunk_id == first.chunk_id


@pytest.mark.asyncio
async def test_answer_generation_uses_sources_and_keeps_language(monkeypatch):
    async def fake_complete(**kwargs):
        assert kwargs["response_format"] == {"type": "json_object"}
        assert "Sources:" in kwargs["messages"][1]["content"]
        return json.dumps(
            {
                "answer": "Срок сдачи - пятница [1].",
                "confidence": "high",
                "used_source_numbers": [1],
            }
        )

    monkeypatch.setattr("app.services.answer_generator.complete", fake_complete)

    generated = await AnswerGenerator(model="answer-model").generate_answer(
        question="Когда дедлайн?",
        chunks=[
            RerankedChunk(
                **make_retrieved_chunk(
                    "Срок сдачи проекта - пятница.",
                    score=0.9,
                ).__dict__
            )
        ],
    )

    assert generated.answer == "Срок сдачи - пятница [1]."
    assert generated.confidence == "medium"
    assert generated.used_source_numbers == [1]


@pytest.mark.asyncio
async def test_answer_generation_insufficient_context_returns_low(monkeypatch):
    async def fake_complete(**kwargs):
        _ = kwargs
        return json.dumps(
            {
                "answer": "В источниках недостаточно информации для ответа.",
                "confidence": "medium",
                "used_source_numbers": [],
            }
        )

    monkeypatch.setattr("app.services.answer_generator.complete", fake_complete)

    generated = await AnswerGenerator().generate_answer(
        question="Когда экзамен?",
        chunks=[RerankedChunk(**make_retrieved_chunk("Only homework notes.").__dict__)],
    )

    assert generated.confidence == "low"
    assert generated.used_source_numbers == []
    assert "недостаточно" in generated.answer


@pytest.mark.asyncio
async def test_answer_generation_provider_error_raises_503_error(monkeypatch):
    async def fake_complete(**kwargs):
        _ = kwargs
        raise RuntimeError("llm down")

    monkeypatch.setattr("app.services.answer_generator.complete", fake_complete)

    with pytest.raises(LLMProviderError):
        await AnswerGenerator().generate_answer(
            question="What is the deadline?",
            chunks=[
                RerankedChunk(**make_retrieved_chunk("Deadline is Friday.").__dict__)
            ],
        )


class FakeDocumentRepository:
    def __init__(self, documents=None, ready_count=1):
        self.documents = documents or []
        self.ready_count = ready_count
        self.requested_document_ids = None
        self.count_document_ids = None

    async def list_by_ids_for_user(self, document_ids, user_id):
        self.requested_document_ids = document_ids
        return [document for document in self.documents if document.user_id == user_id]

    async def count_ready_by_user(self, user_id, document_ids=None):
        _ = user_id
        self.count_document_ids = document_ids
        return self.ready_count


class FakeEmbeddingService:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.texts = []

    async def embed_texts(self, texts):
        self.texts = texts
        if self.error is not None:
            raise self.error
        return [[0.1, 0.2, 0.3]]


class FakeVectorSearch:
    def __init__(self, chunks=None):
        self.chunks = chunks or []
        self.calls = []

    async def search(self, **kwargs):
        self.calls.append(kwargs)
        return self.chunks


class FakeQueryRewriter:
    async def rewrite(self, question):
        _ = question
        return "rewritten query"


class FakeAnswerGenerator:
    async def generate_answer(self, question, chunks):
        _ = question, chunks
        from app.services.rag_types import GeneratedAnswer

        return GeneratedAnswer(
            answer="Ответ из второго источника [2].",
            confidence="high",
            used_source_numbers=[2],
            context_source_count=len(chunks),
        )


def make_document(document_id, user_id) -> Document:
    now = datetime.now(timezone.utc)
    return Document(
        id=document_id,
        user_id=user_id,
        title="Mine",
        filename="mine.txt",
        content_type="text/plain",
        size_bytes=10,
        source_type="upload",
        status="ready",
        chunks_count=1,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_rag_agent_rejects_foreign_document_id():
    user_id = uuid4()
    foreign_document_id = uuid4()
    repo = FakeDocumentRepository(documents=[])
    agent = RAGAgent(
        document_repository=repo,
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorSearch(),
        query_rewriter=FakeQueryRewriter(),
    )

    with pytest.raises(RAGDocumentAccessError):
        await agent.answer_question(
            user_id=user_id,
            question="question",
            document_ids=[foreign_document_id],
        )


@pytest.mark.asyncio
async def test_rag_agent_no_ready_documents_skips_external_calls():
    user_id = uuid4()
    embeddings = FakeEmbeddingService()
    vector_search = FakeVectorSearch()
    agent = RAGAgent(
        document_repository=FakeDocumentRepository(ready_count=0),
        embedding_service=embeddings,
        vector_index=vector_search,
        query_rewriter=FakeQueryRewriter(),
    )

    answer = await agent.answer_question(user_id=user_id, question="Что про сроки?")

    assert answer.confidence == "low"
    assert answer.sources == []
    assert embeddings.texts == []
    assert vector_search.calls == []


@pytest.mark.asyncio
async def test_rag_agent_returns_honest_answer_when_vector_search_has_no_chunks():
    user_id = uuid4()
    agent = RAGAgent(
        document_repository=FakeDocumentRepository(ready_count=1),
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorSearch(chunks=[]),
        query_rewriter=FakeQueryRewriter(),
    )

    answer = await agent.answer_question(user_id=user_id, question="Что про сроки?")

    assert answer.confidence == "low"
    assert answer.sources == []
    assert answer.rewritten_query == "rewritten query"
    assert "не нашёл" in answer.answer


@pytest.mark.asyncio
async def test_rag_agent_embedding_error_propagates_as_provider_error():
    user_id = uuid4()
    agent = RAGAgent(
        document_repository=FakeDocumentRepository(ready_count=1),
        embedding_service=FakeEmbeddingService(
            error=EmbeddingProviderError("Embedding generation failed")
        ),
        vector_index=FakeVectorSearch(),
        query_rewriter=FakeQueryRewriter(),
    )

    with pytest.raises(EmbeddingProviderError):
        await agent.answer_question(user_id=user_id, question="What is due?")


@pytest.mark.asyncio
async def test_rag_agent_snippets_truncated_and_citations_aligned(monkeypatch):
    monkeypatch.setattr("app.services.rag_agent.settings.RAG_SNIPPET_CHARS", 40)
    first = make_retrieved_chunk("First chunk about something else.", score=0.8)
    second = make_retrieved_chunk(
        "Second chunk has the exact answer and a long explanation that should be cut.",
        score=0.9,
    )

    class StableReranker:
        async def rerank(self, question, rewritten_query, chunks, top_k):
            _ = question, rewritten_query
            return [RerankedChunk(**chunk.__dict__) for chunk in chunks[:top_k]]

    user_id = uuid4()
    agent = RAGAgent(
        document_repository=FakeDocumentRepository(ready_count=1),
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorSearch(chunks=[first, second]),
        query_rewriter=FakeQueryRewriter(),
        reranker=StableReranker(),
        answer_generator=FakeAnswerGenerator(),
    )

    answer = await agent.answer_question(
        user_id=user_id,
        question="Where is the answer?",
        rerank_top_k=2,
    )

    assert answer.answer == "Ответ из второго источника [1]."
    assert len(answer.sources) == 1
    assert answer.sources[0].chunk_id == second.chunk_id
    assert len(answer.sources[0].snippet) <= 40
    assert answer.sources[0].page_number == 2


@pytest.mark.asyncio
async def test_rag_agent_source_order_matches_citation_order():
    first = make_retrieved_chunk("First chunk has background.", score=0.8)
    second = make_retrieved_chunk("Second chunk has the answer.", score=0.9)

    class StableReranker:
        async def rerank(self, question, rewritten_query, chunks, top_k):
            _ = question, rewritten_query, top_k
            return [RerankedChunk(**chunk.__dict__) for chunk in chunks]

    class CitationOrderAnswerGenerator:
        async def generate_answer(self, question, chunks):
            _ = question, chunks
            from app.services.rag_types import GeneratedAnswer

            return GeneratedAnswer(
                answer="Use the second chunk first [2], then the first [1].",
                confidence="high",
                used_source_numbers=[1, 2],
                context_source_count=len(chunks),
            )

    agent = RAGAgent(
        document_repository=FakeDocumentRepository(ready_count=1),
        embedding_service=FakeEmbeddingService(),
        vector_index=FakeVectorSearch(chunks=[first, second]),
        query_rewriter=FakeQueryRewriter(),
        reranker=StableReranker(),
        answer_generator=CitationOrderAnswerGenerator(),
    )

    answer = await agent.answer_question(user_id=uuid4(), question="question")

    assert answer.answer == "Use the second chunk first [1], then the first [2]."
    assert [source.chunk_id for source in answer.sources] == [
        second.chunk_id,
        first.chunk_id,
    ]


class FakeDBResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.query = None

    async def execute(self, query):
        self.query = query
        return FakeDBResult(self.rows)


class FakeChunkRow:
    def __init__(self, user_id, document_id):
        self.id = uuid4()
        self.user_id = user_id
        self.document_id = document_id
        self.chunk_index = 1
        self.content = "Matched content"
        self.chunk_metadata = {"page_number": 5}


@pytest.mark.asyncio
async def test_vector_search_filters_by_user_id_and_document_ids():
    user_id = uuid4()
    document_id = uuid4()
    chunk = FakeChunkRow(user_id=user_id, document_id=document_id)
    db = FakeDB(rows=[(chunk, "Doc", "doc.pdf", 0.15)])

    repo = type("FakeRepo", (), {"db": db})()
    results = await VectorIndexService(repo, embedding_dimensions=3).search(
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
    assert results[0].score == pytest.approx(0.85)
