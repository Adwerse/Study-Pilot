import uuid

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_by_telegram_id(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:
        _ = first_name
        insert_stmt = insert(User).values(
            id=uuid.uuid4(),
            telegram_id=telegram_id,
            username=username,
        )
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[User.telegram_id],
            set_={
                "username": func.coalesce(insert_stmt.excluded.username, User.username)
            },
        ).returning(User.id)
        result = await self.db.execute(upsert_stmt)
        user_id = result.scalar_one()
        await self.db.commit()

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        return user_result.scalar_one()

    async def update_timezone(self, user_id: UUID, timezone_name: str) -> None:
        user = await self.db.get(User, user_id)
        if user is None or user.timezone == timezone_name:
            return

        user.timezone = timezone_name
        await self.db.commit()
