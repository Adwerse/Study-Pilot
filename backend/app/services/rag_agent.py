import logging
import re
from uuid import UUID

from app.config import settings
from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import RAGAnswer, RAGSource
from app.services.answer_generator import AnswerGenerator
from app.services.embedding_service import EmbeddingService
from app.services.query_rewriter import QueryRewriter
from app.services.rag_types import RerankedChunk
from app.services.reranker import Reranker
from app.services.vector_search_service import VectorSearchService


logger = logging.getLogger(__name__)

CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class RAGDocumentAccessError(Exception):
    pass


class RAGAgent:
    def __init__(
        self,
        document_repository: DocumentRepository,
        embedding_service: EmbeddingService,
        vector_search_service: VectorSearchService,
        query_rewriter: QueryRewriter | None = None,
        reranker: Reranker | None = None,
        answer_generator: AnswerGenerator | None = None,
    ):
        self.document_repository = document_repository
        self.embedding_service = embedding_service
        self.vector_search_service = vector_search_service
        self.query_rewriter = query_rewriter or QueryRewriter()
        self.reranker = reranker or Reranker()
        self.answer_generator = answer_generator or AnswerGenerator()

    async def answer_question(
        self,
        user_id: UUID,
        question: str,
        document_ids: list[UUID] | None = None,
        top_k: int = 8,
        rerank_top_k: int = 4,
    ) -> RAGAnswer:
        top_k = max(1, min(top_k, 20))
        rerank_top_k = max(1, min(rerank_top_k, 10))
        scoped_document_ids = await self._validate_document_access(
            user_id=user_id,
            document_ids=document_ids,
        )
        if not await self._has_ready_documents(user_id, scoped_document_ids):
            return self._empty_answer(question=question, rewritten_query=question)

        rewritten_query = await self.query_rewriter.rewrite(question)
        query_embedding = (await self.embedding_service.embed_texts([rewritten_query]))[
            0
        ]
        retrieved_chunks = await self.vector_search_service.search(
            user_id=user_id,
            query_embedding=query_embedding,
            document_ids=scoped_document_ids,
            top_k=top_k,
        )
        if not retrieved_chunks:
            return self._empty_answer(
                question=question,
                rewritten_query=rewritten_query,
            )

        reranked_chunks = await self.reranker.rerank(
            question=question,
            rewritten_query=rewritten_query,
            chunks=retrieved_chunks,
            top_k=rerank_top_k,
        )
        selected_chunks = [
            chunk
            for chunk in reranked_chunks
            if chunk.score >= settings.RAG_MIN_SCORE_THRESHOLD
        ]
        if not selected_chunks:
            return self._empty_answer(
                question=question,
                rewritten_query=rewritten_query,
            )

        generated = await self.answer_generator.generate_answer(
            question=question,
            chunks=selected_chunks,
        )
        context_chunks = selected_chunks[: generated.context_source_count]
        answer, used_chunks = self._align_answer_sources(
            answer=generated.answer,
            used_source_numbers=generated.used_source_numbers,
            context_chunks=context_chunks,
        )

        return RAGAnswer(
            answer=answer,
            sources=[self._build_source(chunk) for chunk in used_chunks],
            rewritten_query=rewritten_query,
            confidence=generated.confidence,
        )

    async def _validate_document_access(
        self,
        user_id: UUID,
        document_ids: list[UUID] | None,
    ) -> list[UUID] | None:
        if document_ids is None:
            return None

        unique_document_ids = list(dict.fromkeys(document_ids))
        documents = await self.document_repository.list_by_ids_for_user(
            document_ids=unique_document_ids,
            user_id=user_id,
        )
        owned_ids = {document.id for document in documents}
        if owned_ids != set(unique_document_ids):
            logger.info("RAG document access denied user_id=%s", user_id)
            raise RAGDocumentAccessError("Document not found")

        return unique_document_ids

    async def _has_ready_documents(
        self,
        user_id: UUID,
        document_ids: list[UUID] | None,
    ) -> bool:
        ready_count = await self.document_repository.count_ready_by_user(
            user_id=user_id,
            document_ids=document_ids,
        )
        return ready_count > 0

    @staticmethod
    def _align_answer_sources(
        answer: str,
        used_source_numbers: list[int],
        context_chunks: list[RerankedChunk],
    ) -> tuple[str, list[RerankedChunk]]:
        if not used_source_numbers:
            return answer, []

        valid_numbers = [
            source_number
            for source_number in used_source_numbers
            if 1 <= source_number <= len(context_chunks)
        ]
        if not valid_numbers:
            return answer, []

        mapping = {
            old_source_number: new_source_number
            for new_source_number, old_source_number in enumerate(
                valid_numbers, start=1
            )
        }

        def replace_citation(match: re.Match[str]) -> str:
            old_source_number = int(match.group(1))
            if old_source_number not in mapping:
                return match.group(0)
            return f"[{mapping[old_source_number]}]"

        aligned_answer = CITATION_PATTERN.sub(replace_citation, answer)
        aligned_chunks = [
            context_chunks[source_number - 1] for source_number in valid_numbers
        ]
        return aligned_answer, aligned_chunks

    @staticmethod
    def _build_source(chunk: RerankedChunk) -> RAGSource:
        return RAGSource(
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            filename=chunk.filename,
            chunk_id=chunk.chunk_id,
            chunk_index=chunk.chunk_index,
            score=round(chunk.score, 4),
            page_number=RAGAgent._metadata_page_number(chunk),
            snippet=RAGAgent._build_snippet(chunk.content),
        )

    @staticmethod
    def _metadata_page_number(chunk: RerankedChunk) -> int | None:
        page_number = chunk.metadata.get("page_number")
        if page_number is None:
            return None
        try:
            return int(page_number)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _build_snippet(content: str) -> str:
        normalized = " ".join(content.split())
        limit = max(1, settings.RAG_SNIPPET_CHARS)
        if len(normalized) <= limit:
            return normalized
        if limit <= 3:
            return normalized[:limit]
        return f"{normalized[: limit - 3].rstrip()}..."

    @staticmethod
    def _empty_answer(question: str, rewritten_query: str) -> RAGAnswer:
        return RAGAnswer(
            answer=AnswerGenerator._no_context_answer(question),
            sources=[],
            rewritten_query=rewritten_query,
            confidence="low",
        )
