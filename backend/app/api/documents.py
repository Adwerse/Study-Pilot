import re
from pathlib import PurePath
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.config import settings
from app.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentSourceType,
    DocumentStatus,
    DocumentUploadResponse,
)
from app.services.document_ingest_service import DocumentIngestService
from app.services.document_text_extractor import (
    DocumentTextExtractor,
    UnsupportedFileTypeError,
)


router = APIRouter(prefix="/documents", tags=["documents"])

FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


async def resolve_user_id(current_user: dict, db: AsyncSession) -> UUID:
    telegram_id = current_user.get("id")
    if telegram_id is None:
        raise HTTPException(status_code=401, detail="Telegram user id missing")

    user_repo = UserRepository(db)
    user = await user_repo.get_or_create_by_telegram_id(
        telegram_id=int(telegram_id),
        username=current_user.get("username"),
        first_name=current_user.get("first_name"),
    )
    return user.id


def build_document_repository(db: AsyncSession) -> DocumentRepository:
    return DocumentRepository(db)


def build_document_ingest_service(db: AsyncSession) -> DocumentIngestService:
    repo = build_document_repository(db)
    return DocumentIngestService(document_repository=repo)


def sanitize_upload_filename(filename: str | None) -> str:
    raw_name = PurePath(filename or "document").name.strip()
    safe_name = FILENAME_SAFE_PATTERN.sub("_", raw_name).strip(" .")
    if not safe_name:
        return "document"

    if len(safe_name) <= 255:
        return safe_name

    suffix = PurePath(safe_name).suffix[:24]
    stem_limit = max(1, 255 - len(suffix))
    return f"{PurePath(safe_name).stem[:stem_limit]}{suffix}"


def normalize_title(title: str | None, filename: str) -> str:
    normalized = title.strip() if isinstance(title, str) else ""
    if not normalized:
        normalized = PurePath(filename).stem or filename
    return normalized[:255] or "Untitled document"


def parse_tags(tags: str | None) -> list[str] | None:
    if not tags:
        return None
    parsed = [tag.strip()[:50] for tag in tags.split(",") if tag.strip()]
    return parsed[:20] or None


async def read_upload_file(file: UploadFile) -> bytes:
    file_bytes = await file.read(settings.DOCUMENT_MAX_FILE_SIZE_BYTES + 1)
    await file.close()

    if len(file_bytes) > settings.DOCUMENT_MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is too large",
        )
    if not file_bytes:
        raise HTTPException(
            status_code=422,
            detail="File is empty",
        )
    return file_bytes


def validate_supported_upload(filename: str, content_type: str) -> None:
    try:
        DocumentTextExtractor.validate_supported_file(filename, content_type)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc


def build_upload_response(document) -> DocumentUploadResponse:
    return DocumentUploadResponse(
        document_id=document.id,
        status=document.status,
        title=document.title,
        filename=document.filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        chunks_count=document.chunks_count,
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    source_type: Annotated[DocumentSourceType, Form()] = "upload",
    tags: Annotated[str | None, Form()] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    filename = sanitize_upload_filename(file.filename)
    content_type = (
        (file.content_type or "application/octet-stream").split(";")[0].strip().lower()
    )
    file_bytes = await read_upload_file(file)
    validate_supported_upload(filename, content_type)

    user_id = await resolve_user_id(current_user, db)
    repo = build_document_repository(db)
    document = await repo.create_document(
        user_id=user_id,
        title=normalize_title(title, filename),
        filename=filename,
        content_type=content_type,
        size_bytes=len(file_bytes),
        source_type=source_type,
        tags=parse_tags(tags),
    )

    ingest_service = build_document_ingest_service(db)
    processed_document = await ingest_service.ingest_document(document.id, file_bytes)
    return build_upload_response(processed_document)


@router.get("", response_model=DocumentListResponse, include_in_schema=False)
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: DocumentStatus | None = Query(default=None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    user_id = await resolve_user_id(current_user, db)
    repo = build_document_repository(db)
    items, total = await repo.list_by_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status_filter,
    )
    return DocumentListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    user_id = await resolve_user_id(current_user, db)
    repo = build_document_repository(db)
    document = await repo.get_by_id(document_id, user_id=user_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
