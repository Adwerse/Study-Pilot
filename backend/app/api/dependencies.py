from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


async def get_current_user(db: AsyncSession = Depends(get_db)) -> None:
    # TODO: валидация Telegram initData
    _ = db
    return None