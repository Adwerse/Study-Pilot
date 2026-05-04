from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.documents import resolve_user_id
from app.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.rag import AskRequest, AskResponse
from app.services.answer_generator import LLMProviderError
from app.services.embedding_service import EmbeddingProviderError, EmbeddingService
from app.services.rag_agent import RAGAgent, RAGDocumentAccessError
from app.services.rag_service import RAGService
from app.services.vector_search_service import VectorSearchError, VectorSearchService


router = APIRouter(
    prefix="/ask", tags=["ask"], dependencies=[Depends(get_current_user)]
)


def build_rag_agent(db: AsyncSession) -> RAGAgent:
    document_repository = DocumentRepository(db)
    return RAGAgent(
        document_repository=document_repository,
        embedding_service=EmbeddingService(),
        vector_search_service=VectorSearchService(db),
    )


def build_rag_service(db: AsyncSession) -> RAGService:
    return RAGService(rag_agent=build_rag_agent(db))


@router.post("", response_model=AskResponse)
@router.post("/", response_model=AskResponse, include_in_schema=False)
async def ask_question(
    body: AskRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AskResponse:
    try:
        user_id = await resolve_user_id(current_user, db)
        rag_service = build_rag_service(db)
        return await rag_service.answer_question(
            user_id=user_id,
            question=body.question,
            document_ids=body.document_ids,
            top_k=body.top_k,
            rerank_top_k=body.rerank_top_k,
        )
    except RAGDocumentAccessError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
    except EmbeddingProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is temporarily unavailable",
        ) from exc
    except VectorSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is temporarily unavailable",
        ) from exc
    except LLMProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is temporarily unavailable",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
