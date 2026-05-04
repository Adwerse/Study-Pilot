from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


DocumentSourceType = Literal["upload", "telegram", "manual"]
DocumentStatus = Literal["processing", "ready", "failed"]
UNSAFE_ERROR_MARKERS = (
    "traceback",
    "api key",
    "authorization",
    "bearer ",
    "password",
    "secret",
    "token",
    "sk-",
)


def sanitize_public_error_message(value: str | None) -> str | None:
    if value is None:
        return None

    message = " ".join(str(value).split())
    if not message:
        return None
    lowered = message.lower()
    if any(marker in lowered for marker in UNSAFE_ERROR_MARKERS):
        return "Document processing failed"
    return message[:500]


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus
    title: str
    filename: str
    content_type: str
    size_bytes: int
    chunks_count: int


class DocumentListItem(BaseModel):
    id: UUID
    title: str
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    chunks_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("error_message", mode="before")
    @classmethod
    def sanitize_error_message(cls, value: str | None) -> str | None:
        return sanitize_public_error_message(value)

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    items: list[DocumentListItem]
    total: int
    limit: int
    offset: int


class DocumentDetailResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    status: DocumentStatus
    chunks_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    @field_validator("error_message", mode="before")
    @classmethod
    def sanitize_error_message(cls, value: str | None) -> str | None:
        return sanitize_public_error_message(value)

    model_config = ConfigDict(from_attributes=True)
