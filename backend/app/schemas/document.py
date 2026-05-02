from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


DocumentSourceType = Literal["upload", "telegram", "manual"]
DocumentStatus = Literal["processing", "ready", "failed"]


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
    status: DocumentStatus
    chunks_count: int
    created_at: datetime

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

    model_config = ConfigDict(from_attributes=True)
