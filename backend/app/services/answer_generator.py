import json
import logging
import re
from typing import Any

from app.agents.llm_client import complete
from app.config import settings
from app.services.rag_types import GeneratedAnswer, RAGConfidence, RerankedChunk


logger = logging.getLogger(__name__)

ANSWER_SYSTEM_PROMPT = (
    "You are the StudyPilot RAG assistant. Answer only from the provided "
    "sources. If there is not enough information, say that directly. Do not "
    "make things up. Answer in English. Use source citations in the format "
    "[1], [2], where the number matches the source order."
)

CITATION_PATTERN = re.compile(r"\[(\d+)\]")
INSUFFICIENT_MARKERS = (
    "not enough",
    "not sufficient",
    "couldn't find",
    "could not find",
    "no relevant",
    "do not contain",
)


class LLMProviderError(Exception):
    pass


class AnswerGenerator:
    def __init__(
        self,
        model: str | None = None,
        max_context_chars: int | None = None,
    ):
        self.model = model or settings.RAG_ANSWER_MODEL
        self.max_context_chars = max_context_chars or settings.RAG_MAX_CONTEXT_CHARS

    async def generate_answer(
        self,
        question: str,
        chunks: list[RerankedChunk],
    ) -> GeneratedAnswer:
        context_chunks = self._limit_context(chunks)
        if not context_chunks:
            return GeneratedAnswer(
                answer=self._no_context_answer(question),
                confidence="low",
                used_source_numbers=[],
                context_source_count=0,
            )
        if settings.LLM_PROVIDER == "fake":
            return GeneratedAnswer(
                answer="Based on your uploaded material, focus loops connect goals, sessions, notes, and review [1].",
                confidence="high",
                used_source_numbers=[1],
                context_source_count=1,
            )

        prompt = self._build_user_prompt(question, context_chunks)
        try:
            raw = await complete(
                messages=[
                    {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            logger.exception("RAG answer generation failed")
            raise LLMProviderError("Answer generation failed") from exc

        answer, model_confidence, used_source_numbers = self._parse_response(
            raw=raw,
            source_count=len(context_chunks),
        )
        if not answer:
            raise LLMProviderError("Answer generation returned an empty response")

        heuristic_confidence = self._heuristic_confidence(answer, context_chunks)
        confidence = self._merge_confidence(model_confidence, heuristic_confidence)
        if self._is_insufficient_answer(answer):
            used_source_numbers = []
            confidence = "low"

        return GeneratedAnswer(
            answer=answer,
            confidence=confidence,
            used_source_numbers=used_source_numbers,
            context_source_count=len(context_chunks),
        )

    def _limit_context(self, chunks: list[RerankedChunk]) -> list[RerankedChunk]:
        selected: list[RerankedChunk] = []
        current_chars = 0
        for chunk in chunks:
            projected = current_chars + len(chunk.content)
            if selected and projected > self.max_context_chars:
                break
            selected.append(chunk)
            current_chars = projected
            if current_chars >= self.max_context_chars:
                break
        return selected

    @staticmethod
    def _build_user_prompt(question: str, chunks: list[RerankedChunk]) -> str:
        context = "\n\n".join(
            AnswerGenerator._format_context_chunk(index, chunk)
            for index, chunk in enumerate(chunks, start=1)
        )
        return (
            "Question:\n"
            f"{question}\n\n"
            "Sources:\n"
            f"{context}\n\n"
            "Return a JSON object with exactly these fields: "
            "answer (string, with [1] style citations), "
            "confidence (one of low, medium, high), "
            "used_source_numbers (array of source numbers actually used)."
        )

    @staticmethod
    def _format_context_chunk(index: int, chunk: RerankedChunk) -> str:
        page_number = chunk.metadata.get("page_number")
        return (
            f"[{index}] Document: {chunk.document_title} / {chunk.filename}, "
            f"chunk {chunk.chunk_index}, page {page_number}\n"
            f"{chunk.content}"
        )

    @staticmethod
    def _parse_response(
        raw: str | None,
        source_count: int,
    ) -> tuple[str, RAGConfidence | None, list[int]]:
        raw_text = (raw or "").strip()
        if not raw_text:
            return "", None, []

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            answer = raw_text
            return (
                answer,
                None,
                AnswerGenerator._extract_citations(
                    answer,
                    source_count,
                ),
            )

        answer = str(data.get("answer") or "").strip()
        confidence = data.get("confidence")
        if confidence not in {"low", "medium", "high"}:
            confidence = None

        used_source_numbers = AnswerGenerator._normalize_used_sources(
            data.get("used_source_numbers"),
            source_count,
        )
        if not used_source_numbers:
            used_source_numbers = AnswerGenerator._extract_citations(
                answer,
                source_count,
            )

        return answer, confidence, used_source_numbers

    @staticmethod
    def _normalize_used_sources(value: Any, source_count: int) -> list[int]:
        if not isinstance(value, list):
            return []

        normalized: list[int] = []
        for item in value:
            try:
                source_number = int(item)
            except (TypeError, ValueError):
                continue
            if 1 <= source_number <= source_count and source_number not in normalized:
                normalized.append(source_number)
        return normalized

    @staticmethod
    def _extract_citations(answer: str, source_count: int) -> list[int]:
        citations: list[int] = []
        for match in CITATION_PATTERN.findall(answer):
            source_number = int(match)
            if 1 <= source_number <= source_count and source_number not in citations:
                citations.append(source_number)
        return citations

    @staticmethod
    def _heuristic_confidence(
        answer: str,
        chunks: list[RerankedChunk],
    ) -> RAGConfidence:
        if AnswerGenerator._is_insufficient_answer(answer) or not chunks:
            return "low"

        scores = [chunk.score for chunk in chunks]
        best_score = max(scores)
        average_top_two = sum(scores[:2]) / min(2, len(scores))
        if len(chunks) >= 2 and best_score >= 0.75 and average_top_two >= 0.65:
            return "high"
        if best_score >= settings.RAG_MIN_SCORE_THRESHOLD:
            return "medium"
        return "low"

    @staticmethod
    def _merge_confidence(
        model_confidence: RAGConfidence | None,
        heuristic_confidence: RAGConfidence,
    ) -> RAGConfidence:
        if model_confidence is None:
            return heuristic_confidence

        order = {"low": 0, "medium": 1, "high": 2}
        return (
            model_confidence
            if order[model_confidence] <= order[heuristic_confidence]
            else heuristic_confidence
        )

    @staticmethod
    def _is_insufficient_answer(answer: str) -> bool:
        lowered = answer.lower()
        return any(marker in lowered for marker in INSUFFICIENT_MARKERS)

    @staticmethod
    def _no_context_answer(question: str) -> str:
        _ = question
        return "I couldn't find relevant information in the uploaded materials."
