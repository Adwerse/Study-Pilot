from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middlewares.auth import get_telegram_user


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _ = db
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    if authorization.startswith("test "):
        return get_test_user(authorization[5:])

    if not authorization.startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    init_data = authorization[4:]
    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    user_data = get_telegram_user(init_data, settings.telegram_bot_token)
    return user_data


def get_test_user(token: str) -> dict:
    if not settings.is_test_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Test auth is disabled"
        )

    secret, separator, telegram_id = token.partition(":")
    if not separator or secret != settings.TEST_AUTH_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid test authorization",
        )

    try:
        parsed_telegram_id = int(telegram_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid test authorization",
        ) from exc

    return {
        "id": parsed_telegram_id,
        "username": "e2e_tester",
        "first_name": "E2E",
        "timezone": "UTC",
    }
