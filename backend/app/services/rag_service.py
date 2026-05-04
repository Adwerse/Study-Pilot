from uuid import UUID

from app.schemas.rag import AskResponse
from app.services.rag_agent import RAGAgent


class RAGService:
    def __init__(self, rag_agent: RAGAgent):
        self.rag_agent = rag_agent

    async def answer_question(
        self,
        user_id: UUID,
        question: str,
        document_ids: list[UUID] | None = None,
        top_k: int = 8,
        rerank_top_k: int = 4,
    ) -> AskResponse:
        return await self.rag_agent.answer_question(
            user_id=user_id,
            question=question,
            document_ids=document_ids,
            top_k=top_k,
            rerank_top_k=rerank_top_k,
        )
