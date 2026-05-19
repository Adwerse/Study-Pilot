import logging
from typing import Protocol

from openai import AsyncOpenAI

from app.config import settings


logger = logging.getLogger(__name__)


class EmbeddingProviderError(Exception):
    pass


class EmbeddingClientProtocol(Protocol):
    embeddings: object


_client: AsyncOpenAI | None = None


def get_embedding_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


class EmbeddingService:
    def __init__(
        self,
        client: EmbeddingClientProtocol | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ):
        self.client = client
        self.model = model or settings.EMBEDDING_MODEL
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if settings.EMBEDDING_PROVIDER == "fake":
            return [self._fake_embedding() for _ in texts]

        client = self.client or get_embedding_client()
        request_kwargs: dict[str, object] = {
            "model": self.model,
            "input": texts,
        }
        if self.model.startswith("text-embedding-3"):
            request_kwargs["dimensions"] = self.dimensions

        try:
            response = await client.embeddings.create(**request_kwargs)
        except Exception as exc:
            logger.exception("Embedding provider request failed")
            raise EmbeddingProviderError("Embedding generation failed") from exc

        embeddings = [
            item.embedding
            for item in sorted(response.data, key=lambda item: item.index)
        ]
        if len(embeddings) != len(texts):
            raise EmbeddingProviderError(
                "Embedding provider returned an invalid result"
            )

        for embedding in embeddings:
            if len(embedding) != self.dimensions:
                raise EmbeddingProviderError(
                    "Embedding dimensions do not match settings"
                )

        return embeddings

    def _fake_embedding(self) -> list[float]:
        dimensions = max(1, int(self.dimensions))
        return [1.0] + [0.0] * (dimensions - 1)
