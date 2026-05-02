import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePath

from pypdf import PdfReader


class UnsupportedFileTypeError(Exception):
    pass


class EmptyDocumentError(Exception):
    pass


class TextExtractionError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedPageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractedDocumentText:
    text: str
    pages: list[ExtractedPageText] | None = None
    metadata: dict[str, str | int] | None = None


SUPPORTED_CONTENT_TYPES: dict[str, set[str]] = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {
        "text/markdown",
        "text/x-markdown",
        "text/plain",
        "application/octet-stream",
    },
    ".pdf": {"application/pdf", "application/octet-stream"},
}


class DocumentTextExtractor:
    supported_extensions = frozenset(SUPPORTED_CONTENT_TYPES.keys())

    def extract(
        self, file_bytes: bytes, filename: str, content_type: str | None
    ) -> ExtractedDocumentText:
        extension = self._get_supported_extension(filename, content_type)
        if extension in {".txt", ".md"}:
            return self._extract_text_file(file_bytes, extension)
        if extension == ".pdf":
            return self._extract_pdf(file_bytes)
        raise UnsupportedFileTypeError("Unsupported file type")

    @classmethod
    def validate_supported_file(cls, filename: str, content_type: str | None) -> None:
        cls._get_supported_extension(filename, content_type)

    @classmethod
    def _get_supported_extension(cls, filename: str, content_type: str | None) -> str:
        safe_name = PurePath(filename or "").name
        extension = PurePath(safe_name).suffix.lower()
        if extension not in cls.supported_extensions:
            raise UnsupportedFileTypeError("Unsupported file extension")

        normalized_content_type = (content_type or "").split(";")[0].strip().lower()
        if normalized_content_type not in SUPPORTED_CONTENT_TYPES[extension]:
            raise UnsupportedFileTypeError("Unsupported file content type")

        return extension

    def _extract_text_file(
        self, file_bytes: bytes, extension: str
    ) -> ExtractedDocumentText:
        try:
            raw_text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TextExtractionError("Text documents must be UTF-8 encoded") from exc

        text = self._normalize_text(raw_text)
        if not text.strip():
            raise EmptyDocumentError("Document does not contain extractable text")

        return ExtractedDocumentText(text=text, metadata={"extension": extension})

    def _extract_pdf(self, file_bytes: bytes) -> ExtractedDocumentText:
        try:
            reader = PdfReader(BytesIO(file_bytes))
        except Exception as exc:
            raise TextExtractionError("PDF could not be read") from exc

        pages: list[ExtractedPageText] = []
        for index, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:
                raise TextExtractionError("PDF text extraction failed") from exc

            normalized_page_text = self._normalize_text(page_text)
            if normalized_page_text.strip():
                pages.append(
                    ExtractedPageText(page_number=index, text=normalized_page_text)
                )

        if not pages:
            raise EmptyDocumentError("PDF does not contain extractable text")

        return ExtractedDocumentText(
            text="\n\n".join(page.text for page in pages),
            pages=pages,
            metadata={"extension": ".pdf", "pages_count": len(reader.pages)},
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[^\S\n]+", " ", normalized)
        normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()
