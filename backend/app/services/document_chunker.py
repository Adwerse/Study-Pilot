from dataclasses import dataclass, replace

from app.config import settings


class DocumentChunkingError(Exception):
    pass


@dataclass(frozen=True)
class DocumentChunkInput:
    chunk_index: int
    content: str
    token_count: int | None
    metadata: dict[str, str | int | None]


class DocumentChunker:
    def __init__(
        self,
        chunk_size_chars: int | None = None,
        chunk_overlap_chars: int | None = None,
        max_chunks: int | None = None,
    ):
        self.chunk_size_chars = chunk_size_chars or settings.DOCUMENT_CHUNK_SIZE_CHARS
        self.chunk_overlap_chars = (
            chunk_overlap_chars
            if chunk_overlap_chars is not None
            else settings.DOCUMENT_CHUNK_OVERLAP_CHARS
        )
        self.max_chunks = max_chunks or settings.DOCUMENT_MAX_CHUNKS

        if self.chunk_size_chars <= 0:
            raise ValueError("chunk_size_chars must be positive")
        if self.chunk_overlap_chars < 0:
            raise ValueError("chunk_overlap_chars cannot be negative")
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError(
                "chunk_overlap_chars must be smaller than chunk_size_chars"
            )

    def chunk_text(
        self, text: str, metadata: dict[str, str | int | None] | None = None
    ) -> list[DocumentChunkInput]:
        normalized = text.strip()
        if not normalized:
            return []

        chunks: list[DocumentChunkInput] = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            if len(chunks) >= self.max_chunks:
                raise DocumentChunkingError("Document is too large to process")

            end = min(start + self.chunk_size_chars, text_length)
            if end < text_length:
                end = self._find_breakpoint(normalized, start, end)

            content = normalized[start:end].strip()
            if content:
                chunks.append(
                    DocumentChunkInput(
                        chunk_index=len(chunks),
                        content=content,
                        token_count=self._estimate_token_count(content),
                        metadata=dict(metadata or {}),
                    )
                )

            if end >= text_length:
                break

            next_start = max(0, end - self.chunk_overlap_chars)
            next_start = self._adjust_start_to_word_boundary(
                normalized, next_start, end
            )
            if next_start <= start:
                next_start = end
            start = next_start

        return chunks

    def reindex_chunks(
        self, chunks: list[DocumentChunkInput]
    ) -> list[DocumentChunkInput]:
        return [replace(chunk, chunk_index=index) for index, chunk in enumerate(chunks)]

    def _find_breakpoint(self, text: str, start: int, hard_end: int) -> int:
        segment = text[start:hard_end]
        minimum_break = max(1, int(self.chunk_size_chars * 0.55))
        break_candidates = [
            segment.rfind("\n\n"),
            segment.rfind(". "),
            segment.rfind("! "),
            segment.rfind("? "),
            segment.rfind("; "),
            segment.rfind(", "),
            segment.rfind(" "),
        ]

        for candidate in break_candidates:
            if candidate >= minimum_break:
                return start + candidate + 1

        return hard_end

    @staticmethod
    def _adjust_start_to_word_boundary(text: str, start: int, previous_end: int) -> int:
        if start <= 0 or start >= len(text) or text[start].isspace():
            return start

        next_space = text.find(" ", start, previous_end)
        if next_space == -1:
            return start
        return next_space + 1

    @staticmethod
    def _estimate_token_count(text: str) -> int:
        return max(1, len(text) // 4)
