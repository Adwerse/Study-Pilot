from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user


router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)) -> dict[str, int | str | None]:
	return {
		"telegram_id": current_user.get("id"),
		"username": current_user.get("username"),
		"first_name": current_user.get("first_name"),
	}


@router.put("/me", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def update_me() -> dict[str, str]:
	return {"detail": "not implemented"}


@router.delete("/me", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def delete_me() -> dict[str, str]:
	return {"detail": "not implemented"}
