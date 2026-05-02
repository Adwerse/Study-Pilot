import pytest

from app.services.document_chunker import DocumentChunker, DocumentChunkingError
from app.services.document_text_extractor import (
    DocumentTextExtractor,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)


def test_text_extractor_decodes_utf8_text():
    extractor = DocumentTextExtractor()

    extracted = extractor.extract(
        "Line one\r\n\r\nLine   two".encode(),
        filename="notes.txt",
        content_type="text/plain",
    )

    assert extracted.text == "Line one\n\nLine two"
    assert extracted.metadata == {"extension": ".txt"}


def test_text_extractor_rejects_unsupported_file_type():
    extractor = DocumentTextExtractor()

    with pytest.raises(UnsupportedFileTypeError):
        extractor.extract(b"hello", filename="notes.exe", content_type="text/plain")


def test_text_extractor_rejects_empty_text():
    extractor = DocumentTextExtractor()

    with pytest.raises(EmptyDocumentError):
        extractor.extract(b"   \n\n", filename="notes.md", content_type="text/markdown")


def test_chunker_creates_metadata_rich_chunks():
    chunker = DocumentChunker(chunk_size_chars=45, chunk_overlap_chars=8, max_chunks=10)
    text = (
        "First paragraph has useful context. "
        "Second sentence continues it.\n\n"
        "Another paragraph should land in a later chunk."
    )

    chunks = chunker.chunk_text(
        text, metadata={"filename": "notes.md", "source_type": "upload"}
    )

    assert len(chunks) > 1
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.content for chunk in chunks)
    assert chunks[0].metadata["filename"] == "notes.md"
    assert chunks[0].metadata["source_type"] == "upload"


def test_chunker_enforces_max_chunks():
    chunker = DocumentChunker(chunk_size_chars=20, chunk_overlap_chars=5, max_chunks=1)

    with pytest.raises(DocumentChunkingError):
        chunker.chunk_text("word " * 30)
