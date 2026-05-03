import logging

from app.agents.llm_client import complete
from app.config import settings


logger = logging.getLogger(__name__)


REWRITE_PROMPT = (
    "Rewrite the user's question into a concise semantic search query. "
    "Keep the original language. Do not answer the question. Do not add facts. "
    "Return only the rewritten query."
)


class QueryRewriter:
    def __init__(self, model: str | None = None):
        self.model = model or settings.RAG_REWRITE_MODEL

    async def rewrite(self, question: str) -> str:
        try:
            rewritten = await complete(
                messages=[
                    {"role": "system", "content": REWRITE_PROMPT},
                    {"role": "user", "content": question},
                ],
                model=self.model,
                temperature=0.0,
                max_tokens=120,
            )
        except Exception:
            logger.warning(
                "RAG query rewrite failed; using original question", exc_info=True
            )
            return question

        normalized = self._normalize_rewritten_query(rewritten)
        return normalized or question

    @staticmethod
    def _normalize_rewritten_query(value: str | None) -> str:
        if not value:
            return ""

        normalized = " ".join(value.strip().strip("`\"'").split())
        if len(normalized) <= 300:
            return normalized

        return normalized[:300].rstrip()
