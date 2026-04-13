from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user


router = APIRouter(prefix="/ask", tags=["ask"], dependencies=[Depends(get_current_user)])


@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def ask_question() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.post("/documents", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def upload_document() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.get("/documents", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_documents() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.delete("/documents/{doc_id}", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def delete_document(doc_id: int) -> dict[str, str]:
	_ = doc_id
	return {"detail": "not implemented"}
